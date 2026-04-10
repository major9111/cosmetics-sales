"""
apps/stock/restock_api.py
=========================
API endpoint that receives approved items from the Receipt Scanner UI
and applies them to the central stock database.

URL: POST /api/stock/restock/
Auth: JWT or Session
"""

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json

from apps.stock.models import Stock, StockLog
from apps.products.models import Product, Category
from apps.branches.models import Branch


@method_decorator([login_required, csrf_exempt], name='dispatch')
class BulkRestockView(View):
    """
    Receives a list of approved receipt items and restocks the correct branch.

    Request body:
    {
      "branch_id": 1,
      "receipt_no": "INV-2024-001",
      "supplier": "Beauty Wholesale Ltd",
      "items": [
        {
          "name": "Nivea Body Lotion",
          "brand": "Nivea",
          "category": "Skincare",
          "quantity": 24,
          "unit": "pieces",
          "unit_cost": 850.00
        },
        ...
      ]
    }

    Response:
    {
      "success": true,
      "restocked": 5,
      "skipped": 0,
      "new_products": 2,
      "details": [...]
    }
    """

    @transaction.atomic
    def post(self, request):
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        branch_id = body.get("branch_id")
        items     = body.get("items", [])
        receipt_no = body.get("receipt_no", "")
        supplier   = body.get("supplier", "")

        if not branch_id:
            return JsonResponse({"success": False, "error": "branch_id is required"}, status=400)

        try:
            branch = Branch.objects.get(id=branch_id, is_active=True)
        except Branch.DoesNotExist:
            return JsonResponse({"success": False, "error": "Branch not found"}, status=404)

        results = []
        new_products = 0
        skipped = 0

        for item_data in items:
            name     = item_data.get("name", "").strip()
            brand    = item_data.get("brand", "").strip()
            quantity = int(item_data.get("quantity", 1))
            unit_cost = float(item_data.get("unit_cost", 0))
            category_name = item_data.get("category", "Other")

            if not name or quantity <= 0:
                skipped += 1
                continue

            # ── Find or create category ────────────────────────────────────
            category, _ = Category.objects.get_or_create(name=category_name)

            # ── Find or create product (match by name + brand) ─────────────
            product_qs = Product.objects.filter(name__iexact=name, is_active=True)
            if brand:
                product_qs = product_qs.filter(brand__iexact=brand)

            product = product_qs.first()

            if not product:
                # Auto-create the product from receipt data
                product = Product.objects.create(
                    name=name,
                    brand=brand,
                    category=category,
                    cost_price=unit_cost or 0,
                    selling_price=unit_cost * 1.3 if unit_cost else 0,  # 30% markup default
                    ai_detected=True,
                )
                new_products += 1

            # ── Restock the stock record ───────────────────────────────────
            stock = Stock.get_or_create_stock(branch=branch, product=product)
            old_qty = stock.quantity

            stock.quantity += quantity
            stock.save()

            # Log the restock
            StockLog.objects.create(
                stock=stock,
                change=quantity,
                reason=StockLog.Reason.RESTOCK,
                note=f"Receipt scan | Supplier: {supplier} | Receipt: {receipt_no}",
                performed_by=request.user,
            )

            results.append({
                "product_id":   product.id,
                "product_name": product.name,
                "brand":        product.brand,
                "quantity_added": quantity,
                "old_quantity": old_qty,
                "new_quantity": old_qty + quantity,
                "new_product":  new_products > 0 and product.id == product.id,
            })

        return JsonResponse({
            "success":      True,
            "branch":       branch.name,
            "restocked":    len(results),
            "skipped":      skipped,
            "new_products": new_products,
            "receipt_no":   receipt_no,
            "supplier":     supplier,
            "details":      results,
        })


# ─── URL registration ──────────────────────────────────────────────────────────
# In apps/stock/api_urls.py:
#
# from django.urls import path
# from .restock_api import BulkRestockView
#
# urlpatterns = [
#     path('restock/', BulkRestockView.as_view(), name='bulk-restock'),
# ]
#
# In cosmetica/urls.py this maps to: POST /api/stock/restock/
