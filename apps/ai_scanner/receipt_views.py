"""
Receipt Scanner Views
=====================
POST /ai/receipts/upload/          → upload receipt, trigger AI scan
GET  /ai/receipts/<id>/review/     → show item-by-item review page
POST /ai/receipts/item/<id>/approve/ → approve one item (with optional edits)
POST /ai/receipts/item/<id>/reject/  → reject one item
POST /ai/receipts/<id>/apply/       → apply ALL approved items to stock
GET  /ai/receipts/                  → list all scans
"""

import json
import threading
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.utils import timezone

from .receipt_models import ReceiptScan, ReceiptItem
from .receipt_service import scan_receipt_image, scan_receipt_pdf, save_scan_to_db
from apps.products.models import Product


# ─────────────────────────────────────────────────────────────────────────────
# Upload Receipt
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def upload_receipt(request):
    if request.method == 'GET':
        return render(request, 'ai_scanner/upload.html', {
            'branches': request.user.branch if not request.user.is_super_admin else None
        })

    file    = request.FILES.get('receipt_file')
    branch  = request.user.branch
    if request.user.is_super_admin:
        from apps.branches.models import Branch
        branch_id = request.POST.get('branch_id')
        branch = get_object_or_404(Branch, pk=branch_id)

    if not file:
        messages.error(request, "Please select a file.")
        return redirect('receipt_upload')

    # Create scan record
    scan = ReceiptScan.objects.create(
        branch=branch,
        uploaded_by=request.user,
        status='scanning'
    )

    ext = file.name.split('.')[-1].lower()
    if ext == 'pdf':
        scan.pdf = file
    else:
        scan.image = file
    scan.save()

    # Run AI scan in background thread so page doesn't hang
    def run_scan():
        try:
            file.seek(0)
            if ext == 'pdf':
                result = scan_receipt_pdf(file)
            else:
                result = scan_receipt_image(file)
            save_scan_to_db(scan, result)
        except Exception as e:
            scan.status = 'failed'
            scan.note = str(e)
            scan.save()

    t = threading.Thread(target=run_scan)
    t.daemon = True
    t.start()

    messages.success(request, "Receipt uploaded! AI is scanning it now...")
    return redirect('receipt_status', pk=scan.pk)


# ─────────────────────────────────────────────────────────────────────────────
# Scan Status (polling page)
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def receipt_status(request, pk):
    scan = get_object_or_404(ReceiptScan, pk=pk)
    return render(request, 'ai_scanner/status.html', {'scan': scan})


@login_required
def receipt_status_api(request, pk):
    """AJAX endpoint polled by the status page every 2 seconds."""
    scan = get_object_or_404(ReceiptScan, pk=pk)
    return JsonResponse({
        'status': scan.status,
        'items_count': scan.total_items,
        'review_url': f'/ai/receipts/{scan.pk}/review/' if scan.status == 'review' else None
    })


# ─────────────────────────────────────────────────────────────────────────────
# Item-by-Item Review
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def review_receipt(request, pk):
    scan  = get_object_or_404(ReceiptScan, pk=pk)
    items = scan.items.all().select_related('confirmed_product')
    products = Product.objects.filter(is_active=True).values('id', 'name', 'sku', 'selling_price')

    return render(request, 'ai_scanner/review.html', {
        'scan': scan,
        'items': items,
        'products_json': json.dumps(list(products)),
        'total': items.count(),
        'approved': items.filter(status='approved').count(),
        'rejected': items.filter(status='rejected').count(),
        'pending': items.filter(status='pending').count(),
        'applied': items.filter(status='applied').count(),
    })


# ─────────────────────────────────────────────────────────────────────────────
# Approve One Item
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def approve_item(request, item_id):
    item = get_object_or_404(ReceiptItem, pk=item_id)
    data = json.loads(request.body)

    product_id = data.get('product_id')
    quantity   = data.get('quantity')
    unit_cost  = data.get('unit_cost')

    if product_id:
        try:
            item.confirmed_product = Product.objects.get(pk=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found.'}, status=404)

    if quantity:
        item.confirmed_quantity = quantity
    if unit_cost:
        item.confirmed_unit_cost = unit_cost

    item.status = 'approved'
    item.save()

    return JsonResponse({
        'success': True,
        'item_id': item.pk,
        'status': 'approved',
        'product_name': item.confirmed_product.name if item.confirmed_product else item.ai_product_name,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Reject One Item
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def reject_item(request, item_id):
    item = get_object_or_404(ReceiptItem, pk=item_id)
    data = json.loads(request.body)

    item.status = 'rejected'
    item.rejection_reason = data.get('reason', '')
    item.save()

    return JsonResponse({'success': True, 'item_id': item.pk, 'status': 'rejected'})


# ─────────────────────────────────────────────────────────────────────────────
# Apply ALL Approved Items to Stock
# ─────────────────────────────────────────────────────────────────────────────

@login_required
@require_POST
def apply_to_stock(request, pk):
    scan = get_object_or_404(ReceiptScan, pk=pk)
    approved_items = scan.items.filter(status='approved')

    if not approved_items.exists():
        return JsonResponse({'error': 'No approved items to apply.'}, status=400)

    results = []
    errors  = []

    for item in approved_items:
        try:
            item.apply_to_stock(applied_by=request.user)
            results.append({
                'item_id': item.pk,
                'product': item.confirmed_product.name if item.confirmed_product else item.ai_product_name,
                'quantity': int(item.confirmed_quantity or item.ai_quantity),
                'success': True
            })
        except Exception as e:
            errors.append({'item_id': item.pk, 'error': str(e)})

    # Mark scan completed if no pending items remain
    if not scan.items.filter(status='pending').exists():
        scan.status = 'completed'
        scan.completed_at = timezone.now()
        scan.save()

    return JsonResponse({
        'applied': len(results),
        'errors':  errors,
        'results': results,
        'scan_status': scan.status,
    })


# ─────────────────────────────────────────────────────────────────────────────
# Receipt List
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def receipt_list(request):
    user = request.user
    if user.is_super_admin:
        scans = ReceiptScan.objects.all()
    else:
        scans = ReceiptScan.objects.filter(branch=user.branch)
    scans = scans.select_related('branch', 'uploaded_by').order_by('-created_at')
    return render(request, 'ai_scanner/list.html', {'scans': scans})
