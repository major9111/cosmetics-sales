from django.db import models


class AIProductScan(models.Model):
    """Log every AI scan attempt."""
    class Method(models.TextChoices):
        IMAGE   = 'image',   'Image Recognition'
        BARCODE = 'barcode', 'Barcode Lookup'

    image       = models.ImageField(upload_to='ai_scans/', blank=True, null=True)
    barcode     = models.CharField(max_length=100, blank=True)
    method      = models.CharField(max_length=10, choices=Method.choices)
    raw_response = models.TextField(blank=True)  # raw AI JSON response

    # What was detected
    detected_name     = models.CharField(max_length=200, blank=True)
    detected_brand    = models.CharField(max_length=100, blank=True)
    detected_category = models.CharField(max_length=100, blank=True)
    detected_description = models.TextField(blank=True)
    confidence        = models.FloatField(null=True, blank=True)

    # Was it accepted and linked to a product?
    accepted = models.BooleanField(null=True)
    product  = models.ForeignKey(
        'products.Product', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ai_scans'
    )
    scanned_by = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_method_display()}] {self.detected_name or 'Unknown'} ({self.confidence or 0:.0%})"
