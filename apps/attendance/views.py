
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Shift
from apps.accounts.models import User
from apps.branches.models import Branch

@login_required
def attendance_list(request):
    user = request.user
    if user.is_super_admin:
        shifts = Shift.objects.select_related("staff","branch").all()[:200]
        staff_list = User.objects.filter(is_active=True)
    else:
        shifts = Shift.objects.filter(branch=user.branch).select_related("staff","branch")[:100]
        staff_list = User.objects.filter(branch=user.branch, is_active=True)
    
    # Performance summary
    from django.db.models import Count, Sum
    from apps.sales.models import Sale
    from datetime import date, timedelta
    today = date.today()
    month_start = today.replace(day=1)
    
    perf = []
    for s in staff_list:
        sales_count = Sale.objects.filter(cashier=s, created_at__date__gte=month_start).count()
        sales_total = Sale.objects.filter(cashier=s, created_at__date__gte=month_start).aggregate(
            t=Sum("grand_total"))["t"] or 0
        shifts_count = Shift.objects.filter(staff=s, clock_in__date__gte=month_start).count()
        perf.append({"staff": s, "sales_count": sales_count, "sales_total": sales_total, "shifts": shifts_count})
    perf.sort(key=lambda x: x["sales_total"], reverse=True)
    
    # Active shifts
    active = Shift.objects.filter(clock_out__isnull=True).select_related("staff","branch")
    
    return render(request, "attendance/attendance_list.html", {
        "shifts": shifts, "performance": perf, "active_shifts": active
    })

@login_required
def clock_in(request):
    user = request.user
    if not user.branch:
        messages.error(request, "You have no branch assigned.")
        return redirect("attendance_list")
    # Check not already clocked in
    active = Shift.objects.filter(staff=user, clock_out__isnull=True).first()
    if active:
        messages.warning(request, f"You are already clocked in since {active.clock_in.strftime('%H:%M')}.")
        return redirect("attendance_list")
    Shift.objects.create(staff=user, branch=user.branch)
    messages.success(request, f"Clocked in at {timezone.now().strftime('%H:%M')}.")
    return redirect("attendance_list")

@login_required
def clock_out(request):
    user = request.user
    active = Shift.objects.filter(staff=user, clock_out__isnull=True).first()
    if not active:
        messages.warning(request, "You are not currently clocked in.")
        return redirect("attendance_list")
    active.clock_out = timezone.now()
    active.save()
    messages.success(request, f"Clocked out. Duration: {active.duration_hours} hours.")
    return redirect("attendance_list")
