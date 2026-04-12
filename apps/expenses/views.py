
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Expense, ExpenseCategory
from apps.branches.models import Branch

@login_required
def expense_list(request):
    user = request.user
    if user.is_super_admin:
        expenses = Expense.objects.select_related("branch","category","recorded_by").all()
    else:
        expenses = Expense.objects.filter(branch=user.branch).select_related("branch","category","recorded_by")
    categories = ExpenseCategory.objects.all()
    branches = Branch.objects.filter(is_active=True) if user.is_super_admin else None
    
    # Filter
    branch_id = request.GET.get("branch")
    cat_id = request.GET.get("category")
    if branch_id: expenses = expenses.filter(branch_id=branch_id)
    if cat_id: expenses = expenses.filter(category_id=cat_id)
    
    total = sum(e.amount for e in expenses)
    return render(request, "expenses/expense_list.html", {
        "expenses": expenses, "categories": categories, 
        "branches": branches, "total": total
    })

@login_required  
def expense_create(request):
    user = request.user
    branches = Branch.objects.filter(is_active=True) if user.is_super_admin else None
    categories = ExpenseCategory.objects.all()
    if request.method == "POST":
        branch_id = request.POST.get("branch") or (user.branch_id if user.branch else None)
        if not branch_id:
            messages.error(request, "Please select a branch.")
            return redirect("expense_create")
        cat_id = request.POST.get("category") or None
        if not cat_id:
            # Auto create category
            cat_name = request.POST.get("new_category","").strip()
            if cat_name:
                cat, _ = ExpenseCategory.objects.get_or_create(name=cat_name)
                cat_id = cat.id
        Expense.objects.create(
            branch_id=branch_id,
            category_id=cat_id,
            title=request.POST.get("title","").strip(),
            amount=request.POST.get("amount",0),
            date=request.POST.get("date") or timezone.now().date(),
            description=request.POST.get("description","").strip(),
            recorded_by=user,
        )
        messages.success(request, "Expense recorded.")
        return redirect("expense_list")
    return render(request, "expenses/expense_form.html", {
        "branches": branches, "categories": categories,
        "today": timezone.now().date()
    })

@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if not request.user.is_super_admin and not request.user.is_branch_manager:
        messages.error(request, "Access denied.")
        return redirect("expense_list")
    if request.method == "POST":
        expense.delete()
        messages.success(request, "Expense deleted.")
    return redirect("expense_list")
