from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Product

@login_required
def product_list_api(request):
    products = list(Product.objects.filter(is_active=True).values('id','name','sku','brand','selling_price'))
    return JsonResponse({'products': products})

@login_required
def product_detail_api(request, pk):
    try:
        p = Product.objects.get(pk=pk)
        return JsonResponse({'id':p.id,'name':p.name,'sku':p.sku,'selling_price':float(p.selling_price)})
    except Product.DoesNotExist:
        return JsonResponse({'error':'Not found'}, status=404)
