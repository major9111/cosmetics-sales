
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Supplier, PurchaseOrder
from apps.branches.models import Branch

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, "suppliers/supplier_list.html", {"suppliers": suppliers})

@login_required
def supplier_create(request):
    if request.method == "POST":
        Supplier.objects.create(
            name=request.POST.get("name","").strip(),
            phone=request.POST.get("phone","").strip(),
            email=request.POST.get("email","").strip(),
            address=request.POST.get("address","").strip(),
            contact_person=request.POST.get("contact_person","").strip(),
            notes=request.POST.get("notes","").strip(),
        )
        messages.success(request, "Supplier added.")
        return redirect("supplier_list")
    return render(request, "suppliers/supplier_form.html", {"title": "Add Supplier"})

@login_required
def supplier_edit(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.name=request.POST.get("name","").strip()
        supplier.phone=request.POST.get("phone","").strip()
        supplier.email=request.POST.get("email","").strip()
        supplier.address=request.POST.get("address","").strip()
        supplier.contact_person=request.POST.get("contact_person","").strip()
        supplier.notes=request.POST.get("notes","").strip()
        supplier.save()
        messages.success(request, "Supplier updated.")
        return redirect("supplier_list")
    return render(request, "suppliers/supplier_form.html", {"title": "Edit Supplier", "supplier": supplier})

@login_required
def supplier_delete(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    if request.method == "POST":
        supplier.is_active = False
        supplier.save()
        messages.success(request, f"Supplier {supplier.name} removed.")
    return redirect("supplier_list")
