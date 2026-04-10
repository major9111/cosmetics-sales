"""
Custom permission decorators for role-based access.
Usage:
    @super_admin_required
    @branch_manager_required
    @cashier_or_above
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def super_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_super_admin:
            messages.error(request, "Access denied. Super Admin only.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def branch_manager_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.is_super_admin or request.user.is_branch_manager):
            messages.error(request, "Access denied. Branch Manager or above required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def cashier_or_above(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # All roles can access
        return view_func(request, *args, **kwargs)
    return wrapper
