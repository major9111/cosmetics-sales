from django.urls import path
from . import api_views

urlpatterns = [
    path('create/', api_views.create_sale, name='api_create_sale'),
    path('summary/', api_views.sales_summary, name='api_sales_summary'),
]
