from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.utils.decorators import method_decorator
import json
from .models import Sale, SaleItem
from apps.stock.models import Stock
from apps.products.models import Product
from apps.branches.models import Branch

@csrf_exempt
@login_required
def create_sale(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST only'}, status=405)
    try:
        body = json.loads(request.body)
        with transaction.atomic():
            branch = Branch.objects.get(pk=body['branch_id'])
            sale = Sale.objects.create(
                branch=branch,
                cashier=request.user,
                customer_name=body.get('customer_name',''),
                payment_method=body.get('payment_method','cash'),
                amount_paid=body.get('amount_paid',0),
                discount=body.get('discount',0),
            )
            for item in body.get('items', []):
                product = Product.objects.get(pk=item['product_id'])
                SaleItem.objects.create(
                    sale=sale, product=product,
                    quantity=item['quantity'],
                    unit_price=product.selling_price,
                    unit_cost=product.cost_price,
                )
            sale.process()
        return JsonResponse({'success': True, 'receipt_no': sale.receipt_no, 'sale_id': sale.id, 'grand_total': float(sale.grand_total)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
def sales_summary(request):
    from .reports import total_revenue, total_profit
    return JsonResponse({
        'revenue_30d': float(total_revenue(days=30)),
        'profit_30d': float(total_profit(days=30)),
    })
