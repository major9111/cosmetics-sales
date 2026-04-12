
from django.urls import path
from . import views
urlpatterns = [
    path("", views.attendance_list, name="attendance_list"),
    path("clock-in/", views.clock_in, name="clock_in"),
    path("clock-out/", views.clock_out, name="clock_out"),
]
