from django.contrib import admin
from .models import AIProductScan

@admin.register(AIProductScan)
class AIProductScanAdmin(admin.ModelAdmin):
    list_display = ('detected_name', 'method', 'confidence', 'accepted', 'scanned_by', 'created_at')
    list_filter = ('method', 'accepted')
