
from django.db import models
from django.utils import timezone

class Shift(models.Model):
    staff       = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="shifts")
    branch      = models.ForeignKey("branches.Branch", on_delete=models.CASCADE)
    clock_in    = models.DateTimeField(default=timezone.now)
    clock_out   = models.DateTimeField(null=True, blank=True)
    note        = models.TextField(blank=True)

    class Meta:
        ordering = ["-clock_in"]

    def __str__(self):
        return f"{self.staff.username} — {self.clock_in.date()}"

    @property
    def duration_hours(self):
        if self.clock_out:
            delta = self.clock_out - self.clock_in
            return round(delta.total_seconds() / 3600, 1)
        return None

    @property
    def is_active(self):
        return self.clock_out is None


class CommissionRate(models.Model):
    """Commission % per role or per staff member."""
    staff       = models.OneToOneField("accounts.User", on_delete=models.CASCADE, 
                                        related_name="commission_rate", null=True, blank=True)
    role        = models.CharField(max_length=20, blank=True)
    rate        = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.staff.username if self.staff else self.role
        return f"{target} — {self.rate}%"
