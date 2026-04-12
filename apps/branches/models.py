from django.db import models


class Branch(models.Model):
    name     = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    phone    = models.CharField(max_length=20, blank=True)
    email    = models.EmailField(blank=True)
    is_main  = models.BooleanField(default=False)   # True = head office / main store
    is_active = models.BooleanField(default=True)
    daily_target = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Branches'
        ordering = ['-is_main', 'name']

    def __str__(self):
        tag = ' [MAIN]' if self.is_main else ''
        return f"{self.name}{tag}"

    # Total stock value for this branch (calculated centrally)
    def total_stock_value(self):
        from apps.stock.models import Stock
        from django.db.models import Sum, F
        result = (
            Stock.objects
            .filter(branch=self)
            .aggregate(total=Sum(F('quantity') * F('product__cost_price')))
        )
        return result['total'] or 0

    # Total sales for this branch
    def total_sales(self):
        from apps.sales.models import Sale
        from django.db.models import Sum
        result = Sale.objects.filter(branch=self).aggregate(total=Sum('grand_total'))
        return result['total'] or 0
