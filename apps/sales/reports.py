"""
Central Reports Service
=======================
All financial and stock calculations happen HERE, not in branches.
Call these functions from any view.
"""
from django.db.models import Sum, Count, F, Q, Avg
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.sales.models import Sale, SaleItem
from apps.stock.models import Stock
from apps.products.models import Product
from apps.branches.models import Branch


def total_revenue(branch=None, days=30):
    """Total revenue across all branches or a specific branch."""
    since = timezone.now() - timedelta(days=days)
    qs = Sale.objects.filter(status='completed', created_at__gte=since)
    if branch:
        qs = qs.filter(branch=branch)
    return qs.aggregate(total=Sum('grand_total'))['total'] or Decimal('0')


def total_profit(branch=None, days=30):
    """Total profit (revenue - cost) across all or a branch."""
    since = timezone.now() - timedelta(days=days)
    qs = SaleItem.objects.filter(sale__status='completed', sale__created_at__gte=since)
    if branch:
        qs = qs.filter(sale__branch=branch)
    result = qs.aggregate(
        profit=Sum((F('unit_price') - F('unit_cost')) * F('quantity'))
    )
    return result['profit'] or Decimal('0')


def branch_comparison(days=30):
    """Return revenue and profit per branch — for central admin dashboard."""
    since = timezone.now() - timedelta(days=days)
    branches = Branch.objects.filter(is_active=True)
    data = []
    for branch in branches:
        revenue = total_revenue(branch=branch, days=days)
        profit  = total_profit(branch=branch, days=days)
        data.append({
            'branch': branch.name,
            'revenue': float(revenue),
            'profit':  float(profit),
            'sales_count': Sale.objects.filter(
                branch=branch, status='completed', created_at__gte=since
            ).count()
        })
    return sorted(data, key=lambda x: x['revenue'], reverse=True)


def top_selling_products(branch=None, limit=10, days=30):
    since = timezone.now() - timedelta(days=days)
    qs = SaleItem.objects.filter(sale__status='completed', sale__created_at__gte=since)
    if branch:
        qs = qs.filter(sale__branch=branch)
    return (
        qs.values('product__name', 'product__sku')
        .annotate(qty_sold=Sum('quantity'), revenue=Sum(F('quantity') * F('unit_price')))
        .order_by('-qty_sold')[:limit]
    )


def low_stock_alerts(branch=None):
    qs = Stock.objects.filter(quantity__lte=F('low_stock_threshold'))
    if branch:
        qs = qs.filter(branch=branch)
    return qs.select_related('product', 'branch').order_by('quantity')


def stock_value_by_branch():
    """Total stock value per branch (cost_price * quantity)."""
    return (
        Stock.objects
        .values('branch__name')
        .annotate(value=Sum(F('quantity') * F('product__cost_price')))
        .order_by('-value')
    )


def daily_sales_trend(branch=None, days=30):
    """Returns list of {date, total} for charting."""
    today = timezone.now().date()
    data = []
    for i in range(days - 1, -1, -1):
        day = today - timedelta(days=i)
        qs = Sale.objects.filter(created_at__date=day, status='completed')
        if branch:
            qs = qs.filter(branch=branch)
        total = qs.aggregate(t=Sum('grand_total'))['t'] or 0
        data.append({'date': day.strftime('%Y-%m-%d'), 'total': float(total)})
    return data
