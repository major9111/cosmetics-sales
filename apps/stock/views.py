from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from .models import Stock, StockLog, StockTransfer
from apps.products.models import Product
from apps.branches.models import Branch

@login_required
def stock_list(request):
    user = request.user
    if user.is_super_admin:
        stocks = Stock.objects.select_related('product','branch').all()
    else:
        stocks = Stock.objects.filter(branch=user.branch).select_related('product','branch')
    return render(request, 'stock/stock_list.html', {'stocks': stocks})

@login_required
def restock_form(request, product_id):
    from django.contrib import messages
    if request.user.is_store_agent:
        messages.error(request, 'Access denied.')
        return redirect('stock_list')
    product = get_object_or_404(Product, pk=product_id)
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        branch_id = request.POST['branch_id']
        qty = int(request.POST['quantity'])
        note = request.POST.get('note','')
        branch = get_object_or_404(Branch, pk=branch_id)
        stock = Stock.get_or_create_stock(branch=branch, product=product)
        stock.restock(qty, note=note)
        messages.success(request, f'Restocked {qty} units of {product.name}')
        return redirect('stock_list')
    return render(request, 'stock/restock_form.html', {'product': product, 'branches': branches})

@login_required
def transfer_create(request):
    products = Product.objects.filter(is_active=True)
    branches = Branch.objects.filter(is_active=True)
    if request.method == 'POST':
        StockTransfer.objects.create(
            from_branch_id=request.POST['from_branch'],
            to_branch_id=request.POST['to_branch'],
            product_id=request.POST['product'],
            quantity=request.POST['quantity'],
            requested_by=request.user,
        )
        messages.success(request, 'Transfer request created.')
        return redirect('transfer_list')
    return render(request, 'stock/transfer_create.html', {'products': products, 'branches': branches})

@login_required
def transfer_list(request):
    transfers = StockTransfer.objects.select_related('product','from_branch','to_branch').order_by('-created_at')
    return render(request, 'stock/transfer_list.html', {'transfers': transfers})

@login_required
def transfer_approve(request, pk):
    transfer = get_object_or_404(StockTransfer, pk=pk)
    if request.method == 'POST':
        try:
            transfer.complete(approved_by=request.user)
            messages.success(request, 'Transfer completed.')
        except ValueError as e:
            messages.error(request, str(e))
    return redirect('transfer_list')

@login_required
def stock_log(request):
    logs = StockLog.objects.select_related('stock__product','stock__branch','performed_by').order_by('-created_at')[:200]
    return render(request, 'stock/stock_log.html', {'logs': logs})

@login_required
def low_stock_alerts(request):
    alerts = Stock.objects.filter(quantity__lte=F('low_stock_threshold')).select_related('product','branch')
    return render(request, 'stock/low_stock.html', {'alerts': alerts})

@login_required
def receipt_scanner(request):
    branches = Branch.objects.filter(is_active=True)
    return render(request, 'ai_scanner/receipt_scanner.html', {'branches': branches})


@login_required
def stock_adjust(request, pk):
    from django.contrib import messages
    if not request.user.is_super_admin and not request.user.is_branch_manager:
        messages.error(request, 'Only managers can adjust stock.')
        return redirect('stock_list')
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        new_qty = int(request.POST.get('quantity', stock.quantity))
        note    = request.POST.get('note', '').strip()
        diff    = new_qty - stock.quantity
        stock.quantity = new_qty
        stock.save()
        if diff != 0:
            StockLog.objects.create(
                stock=stock, change=diff,
                reason=StockLog.Reason.ADJUSTMENT,
                note=note or f'Manual adjustment by {request.user.username}',
                performed_by=request.user,
            )
        messages.success(request, f'Stock adjusted to {new_qty} units.')
        return redirect('stock_list')
    return render(request, 'stock/stock_adjust.html', {'stock': stock})
