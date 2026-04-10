from django.contrib import admin
from .models import Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'branch', 'cashier', 'grand_total', 'payment_method', 'status', 'created_at')
    list_filter = ('branch', 'status', 'payment_method')
    inlines = [SaleItemInline]
