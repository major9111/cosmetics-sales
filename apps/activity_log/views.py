
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import ActivityLog

@login_required
def activity_log(request):
    if not request.user.is_super_admin:
        from django.contrib import messages
        from django.shortcuts import redirect
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    logs = ActivityLog.objects.select_related("user").all()[:500]
    return render(request, "activity_log/log_list.html", {"logs": logs})
