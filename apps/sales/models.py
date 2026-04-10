from django.db import models
from django.db import transaction
from decimal import Decimal


class Sale(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH     = 'cash',     'Cash'
        TRANSFER = 'transfer', 'Bank Transfer'
        POS      = 'pos',      'POS/Card'
        CREDIT   = 'credit',   'Credit'

    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completed'
        REFUNDED  = 'refunded',  'Refunded'
        VOIDED    = 'voided',    'Voided'

    # Relations
    branch      = models.ForeignKey('branches.Branch', on_delete=models.PROTECT, related_name='sales')
    cashier     = models.ForeignKey('accounts.User', on_delete=models.PROTECT, related_name='sales')
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20, blank=True)

    # Financials (all calculated centrally on save)
    subtotal    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount    = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_rate    = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))  # e.g. 7.5 for 7.5%
    tax_amount  = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    change_due  = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices, default=PaymentMethod.CASH)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.COMPLETED)
    note        = models.TextField(blank=True)
    receipt_no  = models.CharField(max_length=30, unique=True, blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale #{self.receipt_no} | {self.branch.name} | ₦{self.grand_total}"

    def calculate_totals(self):
        """Central calculation of all financial fields."""
        items = self.items.all()
        self.subtotal   = sum(item.line_total for item in items)
        self.tax_amount = (self.subtotal - self.discount) * (self.tax_rate / 100)
        self.grand_total = self.subtotal - self.discount + self.tax_amount
        self.change_due  = max(self.amount_paid - self.grand_total, Decimal('0.00'))

    def save(self, *args, **kwargs):
        if not self.receipt_no:
            import uuid, datetime
            date_str = datetime.date.today().strftime('%Y%m%d')
            self.receipt_no = f"CSM-{date_str}-{str(uuid.uuid4())[:5].upper()}"
        super().save(*args, **kwargs)

    @transaction.atomic
    def process(self):
        """
        Deduct stock for all items atomically.
        Called ONCE after items are added.
        """
        for item in self.items.all():
            from apps.stock.models import Stock
            stock = Stock.get_or_create_stock(self.branch, item.product)
            stock.deduct(item.quantity, sale=self)
        self.calculate_totals()
        self.save()

    @property
    def profit(self):
        return sum(item.profit for item in self.items.all())


class SaleItem(models.Model):
    sale     = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey('products.Product', on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)   # price at time of sale
    unit_cost  = models.DecimalField(max_digits=10, decimal_places=2)   # cost at time of sale

    class Meta:
        unique_together = ('sale', 'product')

    @property
    def line_total(self):
        return self.unit_price * self.quantity

    @property
    def profit(self):
        return (self.unit_price - self.unit_cost) * self.quantity

    def __str__(self):
        return f"{self.quantity}x {self.product.name} @ ₦{self.unit_price}"
