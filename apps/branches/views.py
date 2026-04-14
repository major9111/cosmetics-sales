from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from datetime import timedelta
import json

from apps.branches.models import Branch
from apps.products.models import Product
from apps.stock.models import Stock, StockTransfer
from apps.sales.models import Sale, SaleItem
from apps.accounts.models import User


@login_required
def dashboard(request):
    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # ── Branch scope (admins see all, others see their branch) ───────────────
    if user.is_super_admin:
        branch_filter = Q()
        sale_qs = Sale.objects.all()
        stock_qs = Stock.objects.all()
    else:
        branch_filter = Q(branch=user.branch)
        sale_qs = Sale.objects.filter(branch=user.branch)
        stock_qs = Stock.objects.filter(branch=user.branch)

    # ── KPI Cards ─────────────────────────────────────────────────────────────
    today_sales = sale_qs.filter(
        created_at__date=today, status='completed'
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    month_sales = sale_qs.filter(
        created_at__date__gte=month_ago, status='completed'
    ).aggregate(total=Sum('grand_total'))['total'] or 0

    total_products = Product.objects.filter(is_active=True).count()
    low_stock_count = stock_qs.filter(quantity__lte=F('low_stock_threshold')).count()
    out_of_stock    = stock_qs.filter(quantity=0).count()

    total_staff = User.objects.filter(
        **({} if user.is_super_admin else {'branch': user.branch})
    ).count()

    # ── Sales last 7 days chart data ──────────────────────────────────────────
    sales_chart = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_total = sale_qs.filter(
            created_at__date=day, status='completed'
        ).aggregate(t=Sum('grand_total'))['t'] or 0
        sales_chart.append({'date': day.strftime('%a %d'), 'total': float(day_total)})

    # ── Top 5 selling products ─────────────────────────────────────────────────
    top_products = (
        SaleItem.objects
        .filter(sale__in=sale_qs, sale__created_at__date__gte=month_ago)
        .values('product__name')
        .annotate(qty_sold=Sum('quantity'), revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-qty_sold')[:5]
    )

    # ── Branch performance (admin only) ───────────────────────────────────────
    branch_performance = []
    if user.is_super_admin:
        for branch in Branch.objects.filter(is_active=True):
            b_sales = Sale.objects.filter(branch=branch, status='completed')
            branch_performance.append({
                'name': branch.name,
                'today': float(b_sales.filter(created_at__date=today).aggregate(t=Sum('grand_total'))['t'] or 0),
                'month': float(b_sales.filter(created_at__date__gte=month_ago).aggregate(t=Sum('grand_total'))['t'] or 0),
                'low_stock': Stock.objects.filter(branch=branch, quantity__lte=F('low_stock_threshold')).count(),

            })

    # ── Recent sales ──────────────────────────────────────────────────────────
    recent_sales = sale_qs.select_related('branch', 'cashier').order_by('-created_at')[:8]

    # ── Pending transfers ─────────────────────────────────────────────────────
    pending_transfers = StockTransfer.objects.filter(
        status='pending',
        **({} if user.is_super_admin else {'to_branch': user.branch})
    ).select_related('product', 'from_branch', 'to_branch')[:5]

    context = {
        'today_sales':      today_sales,
        'month_sales':      month_sales,
        'total_products':   total_products,
        'low_stock_count':  low_stock_count,
        'out_of_stock':     out_of_stock,
        'total_staff':      total_staff,
        'sales_chart_json': json.dumps(sales_chart),
        'top_products':     top_products,
        'branch_performance': branch_performance,
        'recent_sales':     recent_sales,
        'pending_transfers': pending_transfers,
        'user':             user,
    }

    return render(request, 'dashboard/index.html', context)
