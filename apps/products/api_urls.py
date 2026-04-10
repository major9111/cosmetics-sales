from django.urls import path
from . import api_views

urlpatterns = [
    path('', api_views.product_list_api, name='api_product_list'),
    path('<int:pk>/', api_views.product_detail_api, name='api_product_detail'),
]
