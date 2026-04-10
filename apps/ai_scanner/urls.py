from django.urls import path
from . import views

urlpatterns = [
    path('scan-image/', views.scan_image_view, name='scan_image'),
    path('scan-barcode/', views.scan_barcode_view, name='scan_barcode'),
    path('history/', views.scan_history, name='scan_history'),
]
