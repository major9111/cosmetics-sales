from django.urls import path
from . import views

urlpatterns = [
    path('', views.sale_list, name='sale_list'),
    path('new/', views.sale_create, name='sale_create'),
    path('<int:pk>/', views.sale_detail, name='sale_detail'),
    path('<int:pk>/receipt/', views.sale_receipt, name='sale_receipt'),
    path('reports/', views.reports, name='reports'),
    path('<int:pk>/void/', views.sale_void, name='sale_void'),
    path('<int:pk>/refund/', views.sale_refund, name='sale_refund'),
]
