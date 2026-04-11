from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from apps.branches.models import Branch

def redirect_home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def user_list(request):
    users = User.objects.select_related('branch').all()
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def user_create(request):
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        password   = request.POST.get('password1', '')
        role       = request.POST.get('role', 'cashier')
        phone      = request.POST.get('phone', '').strip()
        branch_id  = request.POST.get('branch') or None
        email      = request.POST.get('email', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'accounts/user_create.html', {'branches': branches})

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return render(request, 'accounts/user_create.html', {'branches': branches})

        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            phone=phone,
            branch_id=branch_id,
        )
        messages.success(request, f'Staff account for {user.get_full_name() or username} created successfully.')
        return redirect('user_list')

    return render(request, 'accounts/user_create.html', {'branches': branches})

@login_required
def user_edit(request, pk):
    staff_user = get_object_or_404(User, pk=pk)
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        staff_user.username   = request.POST.get('username', staff_user.username).strip()
        staff_user.first_name = request.POST.get('first_name', '').strip()
        staff_user.last_name  = request.POST.get('last_name', '').strip()
        staff_user.role       = request.POST.get('role', staff_user.role)
        staff_user.phone      = request.POST.get('phone', '').strip()
        staff_user.email      = request.POST.get('email', '').strip()
        branch_id = request.POST.get('branch') or None
        staff_user.branch_id  = branch_id
        password = request.POST.get('password', '').strip()
        if password:
            staff_user.set_password(password)
        staff_user.save()
        messages.success(request, f'Staff account for {staff_user.get_full_name() or staff_user.username} updated.')
        return redirect('user_list')
    return render(request, 'accounts/user_edit.html', {'staff_user': staff_user, 'branches': branches})

@login_required
def user_toggle(request, pk):
    staff_user = get_object_or_404(User, pk=pk)
    if staff_user.pk != request.user.pk:
        staff_user.is_active = not staff_user.is_active
        staff_user.save()
        status = 'activated' if staff_user.is_active else 'deactivated'
        messages.success(request, f'Account {staff_user.username} {status}.')
    else:
        messages.error(request, 'You cannot deactivate your own account.')
    return redirect('user_list')


@login_required
def profile(request):
    from django.contrib import messages
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name  = request.POST.get('last_name', '').strip()
        request.user.phone      = request.POST.get('phone', '').strip()
        request.user.email      = request.POST.get('email', '').strip()
        request.user.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'branches': branches})


@login_required
def change_password(request):
    from django.contrib import messages
    from django.contrib.auth import update_session_auth_hash
    if request.method == 'POST':
        current  = request.POST.get('current_password', '')
        new_pass = request.POST.get('new_password', '')
        confirm  = request.POST.get('confirm_password', '')
        if not request.user.check_password(current):
            messages.error(request, 'Current password is incorrect.')
        elif len(new_pass) < 8:
            messages.error(request, 'New password must be at least 8 characters.')
        elif new_pass != confirm:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new_pass)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('profile')
    return render(request, 'accounts/change_password.html')
