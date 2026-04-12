
from django.db import models

class ActivityLog(models.Model):
    user        = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True)
    action      = models.CharField(max_length=200)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.action} — {self.created_at.strftime("%d %b %Y %H:%M")}"
