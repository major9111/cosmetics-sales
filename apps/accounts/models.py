from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN   = 'super_admin',  'Super Admin'
        BRANCH_MANAGER = 'branch_manager', 'Branch Manager'
        CASHIER       = 'cashier',      'Cashier'

    role   = models.CharField(max_length=20, choices=Role.choices, default=Role.CASHIER)
    branch = models.ForeignKey(
        'branches.Branch',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='staff'
    )
    phone  = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # ── Shorthand helpers ──────────────────────────────────────────────────────
    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_branch_manager(self):
        return self.role == self.Role.BRANCH_MANAGER

    @property
    def is_cashier(self):
        return self.role == self.Role.CASHIER

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
