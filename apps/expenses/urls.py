
from django.urls import path
from . import views
urlpatterns = [
    path("", views.expense_list, name="expense_list"),
    path("add/", views.expense_create, name="expense_create"),
    path("<int:pk>/delete/", views.expense_delete, name="expense_delete"),
]
