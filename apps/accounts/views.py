from django.shortcuts import render, redirect
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
            role=role,
            phone=phone,
            branch_id=branch_id,
        )
        messages.success(request, f'Staff account for {user.get_full_name() or username} created successfully.')
        return redirect('user_list')

    return render(request, 'accounts/user_create.html', {'branches': branches})
