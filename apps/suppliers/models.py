
from django.db import models

class Supplier(models.Model):
    name        = models.CharField(max_length=150)
    phone       = models.CharField(max_length=30, blank=True)
    email       = models.EmailField(blank=True)
    address     = models.TextField(blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    notes       = models.TextField(blank=True)
    is_active   = models.BooleanField(default=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def total_supplied_value(self):
        from django.db.models import Sum
        result = self.purchase_orders.aggregate(total=Sum("total_amount"))
        return result["total"] or 0


class PurchaseOrder(models.Model):
    class Status(models.TextChoices):
        PENDING   = "pending",   "Pending"
        RECEIVED  = "received",  "Received"
        CANCELLED = "cancelled", "Cancelled"

    supplier    = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    branch      = models.ForeignKey("branches.Branch", on_delete=models.CASCADE)
    order_date  = models.DateField(auto_now_add=True)
    expected_date = models.DateField(null=True, blank=True)
    status      = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes       = models.TextField(blank=True)
    created_by  = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO-{self.pk} | {self.supplier.name} | {self.get_status_display()}"
