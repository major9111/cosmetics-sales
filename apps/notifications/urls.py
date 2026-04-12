
from django.urls import path
from . import views
urlpatterns = [
    path("", views.notification_list, name="notification_list"),
    path("count/", views.notification_count, name="notification_count"),
    path("clear/", views.notification_clear, name="notification_clear"),
]
