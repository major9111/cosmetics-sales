from django.contrib import admin
from .models import Product, Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'brand', 'category', 'cost_price', 'selling_price', 'is_active')
    list_filter = ('category', 'brand', 'is_active', 'ai_detected')
    search_fields = ('name', 'sku', 'barcode', 'brand')
