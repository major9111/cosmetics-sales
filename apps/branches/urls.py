from django.urls import path
from . import branch_views

urlpatterns = [
    path('', branch_views.branch_list, name='branch_list'),
    path('create/', branch_views.branch_create, name='branch_create'),
    path('<int:pk>/', branch_views.branch_detail, name='branch_detail'),
    path('<int:pk>/edit/', branch_views.branch_edit, name='branch_edit'),
]
