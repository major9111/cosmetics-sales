from django.contrib import admin
from .models import Stock, StockLog, StockTransfer

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('product', 'branch', 'quantity', 'low_stock_threshold', 'is_low')
    list_filter = ('branch',)
    search_fields = ('product__name',)

@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ('stock', 'change', 'reason', 'performed_by', 'created_at')
    list_filter = ('reason',)

@admin.register(StockTransfer)
class StockTransferAdmin(admin.ModelAdmin):
    list_display = ('product', 'from_branch', 'to_branch', 'quantity', 'status', 'created_at')
    list_filter = ('status',)
