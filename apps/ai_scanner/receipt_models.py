from django.db import models
from django.contrib.postgres.fields import ArrayField


class ReceiptScan(models.Model):
    """
    Represents one uploaded supplier receipt (image or PDF).
    The AI reads it, extracts items, and the user approves each one before stock is updated.
    """
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending AI Scan'
        SCANNING   = 'scanning',   'AI Scanning...'
        REVIEW     = 'review',     'Awaiting Review'
        PARTIAL    = 'partial',    'Partially Approved'
        COMPLETED  = 'completed',  'Completed'
        FAILED     = 'failed',     'Scan Failed'

    branch       = models.ForeignKey('branches.Branch', on_delete=models.CASCADE, related_name='receipt_scans')
    uploaded_by  = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True)
    image        = models.ImageField(upload_to='receipts/images/', blank=True, null=True)
    pdf          = models.FileField(upload_to='receipts/pdfs/', blank=True, null=True)
    supplier_name = models.CharField(max_length=150, blank=True)
    receipt_date  = models.DateField(null=True, blank=True)
    raw_ai_response = models.TextField(blank=True)   # full JSON from AI
    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    note         = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Receipt #{self.pk} | {self.branch.name} | {self.get_status_display()}"

    @property
    def total_items(self):
        return self.items.count()

    @property
    def approved_items(self):
        return self.items.filter(status='approved').count()

    @property
    def pending_items(self):
        return self.items.filter(status='pending').count()


class ReceiptItem(models.Model):
    """
    One line item extracted by AI from a receipt.
    User approves/edits/rejects each one individually before stock is updated.
    """
    class Status(models.TextChoices):
        PENDING  = 'pending',  'Pending Review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        APPLIED  = 'applied',  'Applied to Stock'

    scan         = models.ForeignKey(ReceiptScan, on_delete=models.CASCADE, related_name='items')

    # What AI detected
    ai_product_name  = models.CharField(max_length=200)
    ai_brand         = models.CharField(max_length=100, blank=True)
    ai_quantity      = models.DecimalField(max_digits=10, decimal_places=2)
    ai_unit          = models.CharField(max_length=30, blank=True)   # pcs, boxes, kg, etc.
    ai_unit_cost     = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ai_total_cost    = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    ai_confidence    = models.FloatField(default=0.0)   # 0.0 - 1.0

    # User edits (filled during review, fallback to ai_ values)
    confirmed_product = models.ForeignKey(
        'products.Product', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='receipt_items'
    )
    confirmed_quantity = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    confirmed_unit_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    status       = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True)
    applied_at   = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.ai_product_name} × {self.ai_quantity} [{self.get_status_display()}]"

    def apply_to_stock(self, applied_by=None):
        """
        Apply this approved item to the branch stock.
        Uses confirmed values if set, else falls back to AI values.
        """
        from django.db import transaction
        from django.utils import timezone
        from apps.stock.models import Stock, StockLog

        if self.status != self.Status.APPROVED:
            raise ValueError("Item must be approved before applying to stock.")
        if not self.confirmed_product:
            raise ValueError("No product linked. Please match to a product first.")

        qty = int(self.confirmed_quantity or self.ai_quantity)
        cost = self.confirmed_unit_cost or self.ai_unit_cost

        with transaction.atomic():
            stock = Stock.get_or_create_stock(self.scan.branch, self.confirmed_product)
            stock.restock(qty, note=f"Receipt #{self.scan.pk} — AI scan")

            # Log with cost info
            StockLog.objects.filter(stock=stock).order_by('-created_at').first()

            self.status = self.Status.APPLIED
            self.applied_at = timezone.now()
            self.save()
