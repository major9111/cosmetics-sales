"""
receipt_proxy.py
================
Server-side proxy for receipt scanning.
Receives image upload from browser → calls OpenAI GPT-4o Vision → returns JSON.
This keeps the OpenAI API key safe on the server.

URL: POST /ai/scan-receipt/
"""

import base64
import json
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings


RECEIPT_PROMPT = """You are an expert at reading supplier delivery receipts for a cosmetics store.
Read this receipt image carefully and extract ALL product line items.

Return ONLY valid JSON with no markdown fences:
{
  "supplier": "supplier/vendor name if visible else ''",
  "receipt_no": "invoice or receipt number if visible else ''",
  "date": "date on receipt if visible else ''",
  "raw_text": "all readable text from the receipt",
  "items": [
    {
      "name": "product name exactly as written",
      "brand": "brand name if visible else ''",
      "category": "Skincare/Haircare/Makeup/Fragrance/Body Care/Other",
      "quantity": 1,
      "unit": "pieces/boxes/cartons/sachets/kg/litres",
      "unit_cost": 0.00,
      "total_cost": 0.00,
      "confidence": 0.95,
      "notes": "any notes about this item"
    }
  ]
}

Rules:
- Include EVERY line item on the receipt
- quantity must be a number (not string)
- unit_cost and total_cost are numbers (use 0 if not visible, never null)
- confidence is 0.0-1.0 (0.9+ for clear text, 0.5-0.7 for blurry)
- Return ONLY the JSON object, no other text
"""


@csrf_exempt
@login_required
def scan_receipt_proxy(request):
    """
    Receives an image file, sends to OpenAI GPT-4o, returns extracted receipt data.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST required'}, status=405)

    api_key = getattr(settings, 'OPENAI_API_KEY', '')
    if not api_key:
        return JsonResponse({
            'success': False,
            'error': 'OpenAI API key not configured. Add OPENAI_API_KEY to your environment variables.'
        }, status=500)

    image_file = request.FILES.get('receipt_image')
    if not image_file:
        return JsonResponse({'success': False, 'error': 'No image file provided.'}, status=400)

    # Encode image
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    ext = image_file.name.split('.')[-1].lower()
    mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}
    mime_type = mime_map.get(ext, 'image/jpeg')

    payload = {
        "model": "gpt-4o",
        "max_tokens": 2000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": RECEIPT_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        raw_text = response.json()['choices'][0]['message']['content'].strip()
        # Strip markdown fences if present
        raw_text = raw_text.replace('```json', '').replace('```', '').strip()
        result = json.loads(raw_text)
        result['success'] = True
        return JsonResponse(result)

    except requests.exceptions.Timeout:
        return JsonResponse({'success': False, 'error': 'OpenAI request timed out. Try again.'}, status=504)
    except requests.exceptions.HTTPError as e:
        return JsonResponse({'success': False, 'error': f'OpenAI API error: {str(e)}'}, status=502)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'AI could not parse the receipt. Try a clearer image.'}, status=422)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
