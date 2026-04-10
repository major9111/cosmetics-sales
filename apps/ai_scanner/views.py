from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import AIProductScan
from .services import scan_image, scan_barcode

@csrf_exempt
@login_required
def scan_image_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image_file = request.FILES['image']
        try:
            result = scan_image(image_file)
            scan = AIProductScan.objects.create(
                image=image_file,
                method='image',
                raw_response=result.get('raw_response',''),
                detected_name=result.get('name',''),
                detected_brand=result.get('brand',''),
                detected_category=result.get('category',''),
                detected_description=result.get('description',''),
                confidence=result.get('confidence',0),
                scanned_by=request.user,
            )
            return JsonResponse({'success': True, 'scan_id': scan.id, **result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST image file required'}, status=400)

@csrf_exempt
@login_required
def scan_barcode_view(request):
    if request.method == 'POST':
        import json
        body = json.loads(request.body)
        barcode = body.get('barcode','')
        try:
            result = scan_barcode(barcode)
            AIProductScan.objects.create(
                barcode=barcode, method='barcode',
                raw_response=result.get('raw_response',''),
                detected_name=result.get('name',''),
                detected_brand=result.get('brand',''),
                detected_category=result.get('category',''),
                confidence=result.get('confidence',0),
                scanned_by=request.user,
            )
            return JsonResponse({'success': True, **result})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'error': 'POST required'}, status=400)

@login_required
def scan_history(request):
    scans = AIProductScan.objects.select_related('scanned_by','product').order_by('-created_at')[:50]
    return render(request, 'ai_scanner/history.html', {'scans': scans})
