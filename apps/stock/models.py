from django.db import models
from django.db import transaction


class Stock(models.Model):
    """
    Central stock record per product per branch.
    ALL reads/writes go through here — never calculate stock at the branch.
    """
    branch   = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, related_name='stocks')
    product  = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='stocks')
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('branch', 'product')
        ordering = ['branch', 'product']

    def __str__(self):
        return f"{self.product.name} @ {self.branch.name} — qty: {self.quantity}"

    @property
    def is_low(self):
        return self.quantity <= self.low_stock_threshold

    @property
    def is_out(self):
        return self.quantity == 0

    @classmethod
    def get_or_create_stock(cls, branch, product):
        obj, _ = cls.objects.get_or_create(branch=branch, product=product)
        return obj

    @transaction.atomic
    def deduct(self, qty, sale=None):
        """Deduct stock safely; raises ValueError if insufficient."""
        if self.quantity < qty:
            raise ValueError(
                f"Insufficient stock for '{self.product.name}' at '{self.branch.name}'. "
                f"Available: {self.quantity}, requested: {qty}"
            )
        self.quantity -= qty
        self.save()
        StockLog.objects.create(
            stock=self, change=-qty,
            reason=StockLog.Reason.SALE,
            note=f"Sale #{sale.id}" if sale else ''
        )

    @transaction.atomic
    def restock(self, qty, note=''):
        """Add stock (receiving from supplier or transfer)."""
        self.quantity += qty
        self.save()
        StockLog.objects.create(
            stock=self, change=qty,
            reason=StockLog.Reason.RESTOCK,
            note=note
        )


class StockLog(models.Model):
    """Audit trail for every stock change."""
    class Reason(models.TextChoices):
        SALE      = 'sale',      'Sale'
        RESTOCK   = 'restock',   'Restock'
        TRANSFER  = 'transfer',  'Transfer'
        ADJUSTMENT = 'adjustment', 'Manual Adjustment'
        RETURN    = 'return',    'Return'

    stock     = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='logs')
    change    = models.IntegerField()         # positive = in, negative = out
    reason    = models.CharField(max_length=20, choices=Reason.choices)
    note      = models.TextField(blank=True)
    performed_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        direction = '+' if self.change >= 0 else ''
        return f"{self.stock.product.name} | {direction}{self.change} | {self.get_reason_display()}"


class StockTransfer(models.Model):
    """Move stock from one branch to another."""
    class Status(models.TextChoices):
        PENDING   = 'pending',   'Pending'
        APPROVED  = 'approved',  'Approved'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    from_branch = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, related_name='transfers_out')
    to_branch   = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, related_name='transfers_in')
    product     = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity    = models.PositiveIntegerField()
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note        = models.TextField(blank=True)
    requested_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='transfers_requested')
    approved_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='transfers_approved')
    created_at  = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    @transaction.atomic
    def complete(self, approved_by):
        """Execute the transfer atomically."""
        from_stock = Stock.get_or_create_stock(self.from_branch, self.product)
        to_stock   = Stock.get_or_create_stock(self.to_branch, self.product)

        from_stock.deduct(self.quantity, sale=None)
        to_stock.restock(self.quantity, note=f"Transfer from {self.from_branch.name}")

        # Update logs to reflect transfer reason
        StockLog.objects.filter(stock=from_stock).order_by('-created_at').first()

        self.status = self.Status.COMPLETED
        self.approved_by = approved_by
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"Transfer: {self.product.name} | {self.from_branch} → {self.to_branch} | qty:{self.quantity}"
