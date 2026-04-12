
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, "notifications/notification_list.html", {"notifications": notifications})

@login_required
def notification_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})

@login_required  
def notification_clear(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user).delete()
    return redirect("notification_list")
