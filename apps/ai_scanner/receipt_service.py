"""
Receipt Scanner Service
=======================
Reads supplier delivery receipts (image or PDF) using GPT-4o Vision.
Returns structured list of items for user review before stock is updated.

Flow:
  1. User uploads receipt image or PDF
  2. scan_receipt(file) → sends to GPT-4o → returns list of items
  3. Items saved as ReceiptItem objects (status=pending)
  4. User reviews each item in UI (approve / edit / reject)
  5. Approved items → apply_to_stock() → StockLog entry created
"""

import base64
import json
import os
import requests
from django.conf import settings


RECEIPT_PROMPT = """
You are an expert at reading supplier delivery receipts and invoices for a cosmetics store.

Carefully read this receipt image and extract ALL product line items.

Return ONLY a valid JSON object in this exact format — no markdown, no preamble:
{
  "supplier_name": "name of supplier or vendor if visible",
  "receipt_date": "YYYY-MM-DD if visible, else null",
  "currency": "NGN or USD or GBP etc if visible",
  "items": [
    {
      "product_name": "full product name as written",
      "brand": "brand name if visible",
      "quantity": 10,
      "unit": "pcs / boxes / cartons / kg / litres",
      "unit_cost": 1500.00,
      "total_cost": 15000.00,
      "confidence": 0.95
    }
  ],
  "grand_total": 50000.00,
  "notes": "any important notes visible on receipt"
}

Rules:
- confidence is 0.0-1.0. Use 0.9+ only when text is very clear. Use 0.5-0.7 for blurry/partial.
- If a field is not visible, use null — never guess prices.
- quantity must always be a number (not a string).
- Extract EVERY line item, even if confidence is low.
- For cosmetics: lipstick, foundation, powder, serum, cream, perfume, etc are all valid products.
"""


def _encode_image(image_file) -> tuple[str, str]:
    """Returns (base64_data, mime_type)"""
    data = base64.b64encode(image_file.read()).decode('utf-8')
    ext = image_file.name.split('.')[-1].lower()
    mime_map = {
        'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'png': 'image/png', 'webp': 'image/webp',
        'gif': 'image/gif'
    }
    return data, mime_map.get(ext, 'image/jpeg')


def scan_receipt_image(image_file) -> dict:
    """
    Send receipt image to GPT-4o Vision.
    Returns structured dict with supplier info + list of items.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not configured.")

    image_data, mime_type = _encode_image(image_file)

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
                            "detail": "high"   # high detail for better text reading
                        }
                    }
                ]
            }
        ]
    }

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

    # Strip any accidental markdown fences
    raw_text = raw_text.replace('```json', '').replace('```', '').strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {
            "supplier_name": "",
            "receipt_date": None,
            "currency": "NGN",
            "items": [],
            "grand_total": None,
            "notes": "AI could not parse receipt clearly. Please try a clearer image.",
            "parse_error": True
        }

    result['raw_response'] = raw_text
    return result


def scan_receipt_pdf(pdf_file) -> dict:
    """
    Convert PDF pages to images then scan each page.
    Merges items from all pages into one result.
    Requires: pip install pdf2image pillow
    """
    try:
        from pdf2image import convert_from_bytes
        import io
        from PIL import Image

        pdf_bytes = pdf_file.read()
        pages = convert_from_bytes(pdf_bytes, dpi=200)

        all_items = []
        supplier_name = ""
        receipt_date = None
        grand_total = None
        currency = "NGN"

        for i, page in enumerate(pages):
            # Convert PIL image to file-like object
            img_io = io.BytesIO()
            page.save(img_io, format='JPEG', quality=90)
            img_io.seek(0)
            img_io.name = f"page_{i+1}.jpg"

            page_result = scan_receipt_image(img_io)

            if not supplier_name and page_result.get('supplier_name'):
                supplier_name = page_result['supplier_name']
            if not receipt_date and page_result.get('receipt_date'):
                receipt_date = page_result['receipt_date']
            if page_result.get('grand_total') and i == len(pages) - 1:
                grand_total = page_result['grand_total']

            all_items.extend(page_result.get('items', []))

        return {
            "supplier_name": supplier_name,
            "receipt_date": receipt_date,
            "currency": currency,
            "items": all_items,
            "grand_total": grand_total,
            "notes": f"Scanned {len(pages)} page(s) from PDF.",
            "raw_response": f"{len(all_items)} items extracted from {len(pages)} pages"
        }

    except ImportError:
        raise ImportError("pdf2image not installed. Run: pip install pdf2image pillow")


def save_scan_to_db(scan_obj, ai_result: dict):
    """
    Persist AI results into ReceiptScan + ReceiptItem records.
    Called after scan_receipt_image() or scan_receipt_pdf() succeeds.
    """
    from .receipt_models import ReceiptItem
    import datetime

    scan_obj.supplier_name  = ai_result.get('supplier_name', '')
    scan_obj.raw_ai_response = ai_result.get('raw_response', '')

    date_str = ai_result.get('receipt_date')
    if date_str:
        try:
            scan_obj.receipt_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            pass

    scan_obj.status = 'review'
    scan_obj.save()

    # Save each extracted item
    for item_data in ai_result.get('items', []):
        ReceiptItem.objects.create(
            scan=scan_obj,
            ai_product_name=item_data.get('product_name', 'Unknown'),
            ai_brand=item_data.get('brand', ''),
            ai_quantity=item_data.get('quantity', 0),
            ai_unit=item_data.get('unit', 'pcs'),
            ai_unit_cost=item_data.get('unit_cost'),
            ai_total_cost=item_data.get('total_cost'),
            ai_confidence=item_data.get('confidence', 0.5),
        )

    return scan_obj
