from django.contrib import admin
from .models import Branch

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_main', 'is_active')
    list_filter = ('is_main', 'is_active')
