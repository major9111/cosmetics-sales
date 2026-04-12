
from django.db import models

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Expense(models.Model):
    branch      = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="expenses")
    category    = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    title       = models.CharField(max_length=200)
    amount      = models.DecimalField(max_digits=12, decimal_places=2)
    date        = models.DateField()
    description = models.TextField(blank=True)
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.title} — ₦{self.amount}"
