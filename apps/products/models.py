from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name        = models.CharField(max_length=200)
    sku         = models.CharField(max_length=50, unique=True, blank=True)
    barcode     = models.CharField(max_length=100, unique=True, blank=True, null=True)
    category    = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    brand       = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    image       = models.ImageField(upload_to='products/', blank=True, null=True)

    # Pricing
    cost_price    = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    supplier    = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='products'
    )
    expiry_date  = models.DateField(null=True, blank=True)
    reorder_level = models.PositiveIntegerField(default=10)

    # AI-assisted flag
    ai_detected  = models.BooleanField(default=False)
    ai_confidence = models.FloatField(null=True, blank=True)

    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def profit_margin(self):
        if self.cost_price and self.selling_price:
            return round((self.selling_price - self.cost_price) / self.selling_price * 100, 2)
        return 0

    def total_stock(self):
        """Central calculation: sum across ALL branches."""
        from apps.stock.models import Stock
        from django.db.models import Sum
        result = Stock.objects.filter(product=self).aggregate(total=Sum('quantity'))
        return result['total'] or 0

    def stock_in_branch(self, branch):
        """Stock for a specific branch."""
        from apps.stock.models import Stock
        try:
            return Stock.objects.get(product=self, branch=branch).quantity
        except Stock.DoesNotExist:
            return 0

    def save(self, *args, **kwargs):
        # Auto-generate SKU if not set
        if not self.sku:
            prefix = self.name[:3].upper()
            import uuid
            self.sku = f"{prefix}-{str(uuid.uuid4())[:6].upper()}"
        super().save(*args, **kwargs)
