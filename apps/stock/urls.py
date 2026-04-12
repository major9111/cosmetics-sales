from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_list, name='stock_list'),
    path('restock/<int:product_id>/', views.restock_form, name='restock_form'),
    path('transfer/', views.transfer_create, name='transfer_create'),
    path('transfers/', views.transfer_list, name='transfer_list'),
    path('transfers/<int:pk>/approve/', views.transfer_approve, name='transfer_approve'),
    path('log/', views.stock_log, name='stock_log'),
    path('alerts/', views.low_stock_alerts, name='low_stock_alerts'),
    path('receipt-scanner/', views.receipt_scanner, name='receipt_scanner'),
    path('adjust/<int:pk>/', views.stock_adjust, name='stock_adjust'),
    path('reorder/', views.reorder_alerts, name='reorder_alerts'),
    path('expiry/', views.expiry_tracker, name='expiry_tracker'),
]
