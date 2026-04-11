from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sale, SaleItem
from .reports import total_revenue, total_profit, branch_comparison, top_selling_products, daily_sales_trend, low_stock_alerts
from apps.products.models import Product
from apps.branches.models import Branch
import json

@login_required
def sale_list(request):
    from django.core.paginator import Paginator
    from django.contrib import messages
    user = request.user
    if user.is_store_agent:
        messages.error(request, 'Access denied.')
        return redirect('sale_create')
    if user.is_super_admin:
        sales = Sale.objects.select_related('branch','cashier').all()
    else:
        sales = Sale.objects.filter(branch=user.branch).select_related('branch','cashier')
    paginator = Paginator(sales, 20)
    page = paginator.get_page(request.GET.get('page'))
    return render(request, 'sales/sale_list.html', {'sales': page})

@login_required
def sale_create(request):
    user = request.user
    # Guard: cashier/manager must have a branch assigned
    if not user.is_super_admin and not user.branch_id:
        from django.contrib import messages
        messages.error(request, 'You have no branch assigned. Please ask your admin to assign you to a branch before making sales.')
        return redirect('dashboard')

    products = Product.objects.filter(is_active=True).select_related('category')
    branches = Branch.objects.filter(is_active=True) if user.is_super_admin else Branch.objects.filter(pk=user.branch_id)

    # Build stock map: {product_id: {branch_id: qty}} for JS
    from apps.stock.models import Stock
    import json
    stock_map = {}
    for s in Stock.objects.filter(product__is_active=True).values('product_id', 'branch_id', 'quantity'):
        pid = str(s['product_id'])
        bid = str(s['branch_id'])
        if pid not in stock_map:
            stock_map[pid] = {}
        stock_map[pid][bid] = s['quantity']

    return render(request, 'sales/sale_create.html', {
        'products': products,
        'branches': branches,
        'stock_map_json': json.dumps(stock_map),
    })

@login_required
def sale_detail(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/sale_detail.html', {'sale': sale})

@login_required
def sale_receipt(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'sales/receipt.html', {'sale': sale})

@login_required
def reports(request):
    from django.contrib import messages
    user = request.user
    if user.is_store_agent:
        messages.error(request, 'Access denied.')
        return redirect('sale_create')
    branch = None if user.is_super_admin else user.branch
    days = int(request.GET.get('days', 30))
    context = {
        'revenue': total_revenue(branch=branch, days=days),
        'profit': total_profit(branch=branch, days=days),
        'branch_comparison': json.dumps(branch_comparison(days=days)) if user.is_super_admin else '[]',
        'top_products': top_selling_products(branch=branch, days=days),
        'daily_trend': json.dumps(daily_sales_trend(branch=branch, days=days)),
        'low_stock': low_stock_alerts(branch=branch),
        'days': days,
    }
    return render(request, 'sales/reports.html', context)


@login_required
def sale_void(request, pk):
    from django.contrib import messages
    sale = get_object_or_404(Sale, pk=pk)
    if not request.user.is_super_admin and not request.user.is_branch_manager:
        messages.error(request, 'Only managers can void sales.')
        return redirect('sale_detail', pk=pk)
    if sale.status != 'completed':
        messages.error(request, 'Only completed sales can be voided.')
        return redirect('sale_detail', pk=pk)
    if request.method == 'POST':
        from apps.stock.models import Stock, StockLog
        with __import__('django.db', fromlist=['transaction']).transaction.atomic():
            # Restore stock
            for item in sale.items.all():
                stock = Stock.get_or_create_stock(sale.branch, item.product)
                stock.quantity += item.quantity
                stock.save()
                StockLog.objects.create(
                    stock=stock, change=item.quantity,
                    reason=StockLog.Reason.RETURN,
                    note=f'Void of sale {sale.receipt_no}',
                    performed_by=request.user,
                )
            sale.status = 'voided'
            sale.save()
        messages.success(request, f'Sale {sale.receipt_no} has been voided and stock restored.')
        return redirect('sale_detail', pk=pk)
    return render(request, 'sales/sale_void_confirm.html', {'sale': sale})


@login_required
def sale_refund(request, pk):
    from django.contrib import messages
    sale = get_object_or_404(Sale, pk=pk)
    if not request.user.is_super_admin and not request.user.is_branch_manager:
        messages.error(request, 'Only managers can process refunds.')
        return redirect('sale_detail', pk=pk)
    if sale.status != 'completed':
        messages.error(request, 'Only completed sales can be refunded.')
        return redirect('sale_detail', pk=pk)
    if request.method == 'POST':
        from apps.stock.models import Stock, StockLog
        with __import__('django.db', fromlist=['transaction']).transaction.atomic():
            for item in sale.items.all():
                stock = Stock.get_or_create_stock(sale.branch, item.product)
                stock.quantity += item.quantity
                stock.save()
                StockLog.objects.create(
                    stock=stock, change=item.quantity,
                    reason=StockLog.Reason.RETURN,
                    note=f'Refund of sale {sale.receipt_no}',
                    performed_by=request.user,
                )
            sale.status = 'refunded'
            sale.save()
        messages.success(request, f'Sale {sale.receipt_no} refunded and stock restored.')
        return redirect('sale_detail', pk=pk)
    return render(request, 'sales/sale_refund_confirm.html', {'sale': sale})
