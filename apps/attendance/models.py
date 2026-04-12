
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
