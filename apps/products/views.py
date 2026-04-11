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
        Product.objects.create(
            name=request.POST['name'],
            brand=request.POST.get('brand',''),
            cost_price=request.POST['cost_price'],
            selling_price=request.POST['selling_price'],
            category_id=request.POST.get('category') or None,
        )
        return redirect('product_list')
    return render(request, 'products/product_create.html', {'categories': categories})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'products/product_detail.html', {'product': product})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    categories = Category.objects.all()
    if request.method == 'POST':
        product.name = request.POST['name']
        product.brand = request.POST.get('brand','')
        product.cost_price = request.POST['cost_price']
        product.selling_price = request.POST['selling_price']
        product.save()
        return redirect('product_list')
    return render(request, 'products/product_edit.html', {'product': product, 'categories': categories})


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
