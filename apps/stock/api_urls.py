from django.urls import path
from .restock_api import BulkRestockView

urlpatterns = [
    path('restock/', BulkRestockView.as_view(), name='bulk_restock'),
]
