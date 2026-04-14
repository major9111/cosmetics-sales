from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Branch

@login_required
def branch_list(request):
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'branches/branch_list.html', {'branches': branches})

@login_required
def branch_create(request):
    if request.method == 'POST':
        name     = request.POST.get('name', '').strip()
        location = request.POST.get('location', '').strip()
        phone    = request.POST.get('phone', '').strip()
        email    = request.POST.get('email', '').strip()
        is_main  = request.POST.get('is_main') == 'on'

        if not name or not location:
            messages.error(request, 'Branch name and location are required.')
            return render(request, 'branches/branch_create.html')

        # Only one branch can be main store
        if is_main:
            Branch.objects.filter(is_main=True).update(is_main=False)

        branch = Branch.objects.create(
            name=name, location=location,
            phone=phone, email=email, is_main=is_main,
        )
        messages.success(request, f'Branch "{branch.name}" created successfully.')
        return redirect('branch_list')

    return render(request, 'branches/branch_create.html')

@login_required
def branch_detail(request, pk):
    branch = get_object_or_404(Branch, pk=pk)
    return render(request, 'branches/branch_detail.html', {'branch': branch})


@login_required
def branch_edit(request, pk):
    from django.contrib import messages
    if not request.user.is_super_admin:
        messages.error(request, "Only Super Admins can edit branches.")
        return redirect("branch_list")
    branch = get_object_or_404(Branch, pk=pk)
    if request.method == "POST":
        branch.name     = request.POST.get("name", "").strip()
        branch.location = request.POST.get("location", "").strip()
        branch.phone    = request.POST.get("phone", "").strip()
        branch.email    = request.POST.get("email", "").strip()
        branch.is_main  = request.POST.get("is_main") == "on"
        if branch.is_main:
            Branch.objects.exclude(pk=pk).update(is_main=False)
        branch.save()
        messages.success(request, f"Branch {branch.name} updated.")
        return redirect("branch_list")
    return render(request, "branches/branch_edit.html", {"branch": branch})
