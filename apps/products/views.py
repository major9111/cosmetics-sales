from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Product, Category

@login_required
def product_list(request):
    from django.core.paginator import Paginator
    q = request.GET.get('q', '')
    products = Product.objects.filter(is_active=True).select_related('category')
    if q:
        products = products.filter(name__icontains=q)
    paginator = Paginator(products, 25)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'products/product_list.html', {'products': page, 'q': q, 'paginator': paginator})

@login_required
def product_create(request):
    from django.contrib import messages
    if request.user.is_store_agent:
        messages.error(request, 'Access denied.')
        return redirect('stock_list')
    categories = Category.objects.all()
    if request.method == 'POST':
        from apps.suppliers.models import Supplier
        Product.objects.create(
            name=request.POST['name'],
            brand=request.POST.get('brand',''),
            cost_price=request.POST['cost_price'],
            selling_price=request.POST['selling_price'],
            category_id=request.POST.get('category') or None,
            supplier_id=request.POST.get('supplier') or None,
            # expiry_date=request.POST.get('expiry_date') or None,  # Added in batch2
            # reorder_level=int(request.POST.get('reorder_level') or 10),  # Added in batch2
            # barcode=request.POST.get('barcode') or None,
            description=request.POST.get('description',''),
        )
        messages.success(request, 'Product added.')
        return redirect('product_list')
    from apps.suppliers.models import Supplier
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, 'products/product_create.html', {'categories': categories, 'suppliers': suppliers})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        from apps.suppliers.models import Supplier
        product.name = request.POST['name']
        product.brand = request.POST.get('brand','')
        product.cost_price = request.POST['cost_price']
        product.selling_price = request.POST['selling_price']
        product.category_id = request.POST.get('category') or None
        product.supplier_id = request.POST.get('supplier') or None
        product.description = request.POST.get('description','')
        product.save()
        messages.success(request, 'Product updated.')
        return redirect('product_list')
    from apps.suppliers.models import Supplier
    suppliers = Supplier.objects.filter(is_active=True)
    return render(request, 'products/product_edit.html', {'product': product, 'categories': categories, 'suppliers': suppliers})


@login_required
def category_list(request):
    from django.contrib import messages
    if request.user.is_store_agent:
        return redirect('product_list')
    categories = Category.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        desc = request.POST.get('description', '').strip()
        if name:
            if Category.objects.filter(name__iexact=name).exists():
                messages.error(request, f'Category "{name}" already exists.')
            else:
                Category.objects.create(name=name, description=desc)
                messages.success(request, f'Category "{name}" created.')
        return redirect('category_list')
    return render(request, 'products/category_list.html', {'categories': categories})


@login_required
def category_delete(request, pk):
    from django.contrib import messages
    if not request.user.is_super_admin:
        messages.error(request, 'Only Super Admins can delete categories.')
        return redirect('category_list')
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
    return redirect('category_list')


@login_required
def product_import(request):
    from django.contrib import messages
    if request.user.is_store_agent:
        return redirect("product_list")
    if request.method == "POST":
        import csv, io
        f = request.FILES.get("csv_file")
        if not f:
            messages.error(request, "Please upload a CSV file.")
            return redirect("product_import")
        try:
            decoded = f.read().decode("utf-8")
            reader = csv.DictReader(io.StringIO(decoded))
            created = 0
            errors = []
            for i, row in enumerate(reader, 1):
                try:
                    name = row.get("name","").strip()
                    if not name: continue
                    cost  = float(row.get("cost_price", 0) or 0)
                    price = float(row.get("selling_price", 0) or 0)
                    brand = row.get("brand","").strip()
                    cat_name = row.get("category","").strip()
                    cat = None
                    if cat_name:
                        cat, _ = Category.objects.get_or_create(name=cat_name)
                    if not Product.objects.filter(name__iexact=name).exists():
                        Product.objects.create(
                            name=name, brand=brand, category=cat,
                            cost_price=cost, selling_price=price,
                        )
                        created += 1
                except Exception as e:
                    errors.append(f"Row {i}: {e}")
            messages.success(request, f"{created} products imported successfully.")
            if errors:
                messages.warning(request, f"{len(errors)} rows skipped: " + "; ".join(errors[:3]))
        except Exception as e:
            messages.error(request, f"Failed to read CSV: {e}")
        return redirect("product_list")
    return render(request, "products/product_import.html")


@login_required
def product_export(request):
    import csv
    from django.http import HttpResponse
    products = Product.objects.filter(is_active=True).select_related("category","supplier")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=products.csv"
    writer = csv.writer(response)
    writer.writerow(["Name","Brand","Category","Supplier","Cost Price","Selling Price","SKU","Barcode","Reorder Level"])
    for p in products:
        writer.writerow([
            p.name, p.brand,
            p.category.name if p.category else "",
            p.supplier.name if hasattr(p, "supplier") and p.supplier else "",
            p.cost_price, p.selling_price, p.sku, p.barcode or "", 
            getattr(p, "reorder_level", 10)
        ])
    return response


@login_required
def reports_export(request):
    """Export sales report as CSV"""
    import csv
    from django.http import HttpResponse
    from apps.sales.models import Sale
    from django.utils import timezone
    days = int(request.GET.get("days", 30))
    from datetime import timedelta
    since = timezone.now() - timedelta(days=days)
    user = request.user
    if user.is_super_admin:
        sales = Sale.objects.filter(created_at__gte=since).select_related("branch","cashier")
    else:
        sales = Sale.objects.filter(branch=user.branch, created_at__gte=since).select_related("branch","cashier")
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename=sales_report_{days}days.csv"
    writer = csv.writer(response)
    writer.writerow(["Receipt No","Date","Branch","Cashier","Subtotal","Discount","Total","Payment","Status"])
    for s in sales:
        writer.writerow([
            s.receipt_no, s.created_at.strftime("%Y-%m-%d %H:%M"),
            s.branch.name, s.cashier.get_full_name() or s.cashier.username,
            s.subtotal, s.discount, s.grand_total, s.get_payment_method_display(), s.get_status_display()
        ])
    return response
