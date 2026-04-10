"""
AI Scanner Service
==================
Two modes:
  1. scan_image(image_file) → sends image to OpenAI Vision → returns product data
  2. scan_barcode(barcode)  → looks up Open Food Facts / Barcode Lookup → returns product data
"""

import base64
import json
import os
import requests
from django.conf import settings


# ─────────────────────────────────────────────────────────────────────────────
# Image Recognition via OpenAI Vision
# ─────────────────────────────────────────────────────────────────────────────

def scan_image(image_file) -> dict:
    """
    Send a product image to GPT-4o Vision.
    Returns a dict with: name, brand, category, description, confidence
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in settings.")

    # Read and encode image
    image_data = base64.b64encode(image_file.read()).decode('utf-8')
    ext = image_file.name.split('.')[-1].lower()
    mime_map = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'webp': 'image/webp'}
    mime_type = mime_map.get(ext, 'image/jpeg')

    prompt = """
    You are a cosmetics product identifier. Analyze this product image and return ONLY a JSON object with:
    {
      "name": "full product name",
      "brand": "brand name",
      "category": "e.g. Lipstick, Foundation, Moisturizer, Perfume, Skincare, Haircare, etc.",
      "description": "short 1-2 sentence description",
      "confidence": 0.0-1.0
    }
    If you cannot identify the product, return {"name": "", "brand": "", "category": "", "description": "", "confidence": 0.0}
    Return ONLY the JSON object, no other text.
    """

    payload = {
        "model": "gpt-4o",
        "max_tokens": 300,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
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
        timeout=30
    )
    response.raise_for_status()
    data = response.json()
    raw_text = data['choices'][0]['message']['content'].strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError:
        result = {"name": "", "brand": "", "category": "", "description": "", "confidence": 0.0}

    result['raw_response'] = raw_text
    result['method'] = 'image'
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Barcode Lookup via Open Food Facts (free) + AI enrichment fallback
# ─────────────────────────────────────────────────────────────────────────────

def scan_barcode(barcode: str) -> dict:
    """
    Look up a barcode in Open Food Facts API.
    Falls back to OpenAI for enrichment if needed.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    result = {
        "name": "", "brand": "", "category": "",
        "description": "", "confidence": 0.0,
        "raw_response": "", "method": "barcode"
    }

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        result['raw_response'] = json.dumps(data)

        if data.get('status') == 1:
            product = data.get('product', {})
            result['name']        = product.get('product_name', '')
            result['brand']       = product.get('brands', '')
            result['category']    = product.get('categories', '').split(',')[0].strip()
            result['description'] = product.get('generic_name', '')
            result['confidence']  = 0.85  # High confidence for barcode match
        else:
            # Not found — try AI enrichment with barcode number
            result = _ai_enrich_barcode(barcode, result)
    except Exception:
        result = _ai_enrich_barcode(barcode, result)

    return result


def _ai_enrich_barcode(barcode: str, base_result: dict) -> dict:
    """Use GPT to guess product details from barcode if lookup failed."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return base_result

    prompt = f"""
    A cosmetics store product has barcode: {barcode}
    Based on this barcode, return ONLY a JSON object:
    {{
      "name": "likely product name if recognizable",
      "brand": "brand if known",
      "category": "cosmetics category",
      "description": "description",
      "confidence": 0.0-0.3
    }}
    Return ONLY JSON, no other text.
    """

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o", "max_tokens": 200, "messages": [{"role": "user", "content": prompt}]},
            timeout=15
        )
        raw_text = response.json()['choices'][0]['message']['content'].strip()
        data = json.loads(raw_text)
        data['raw_response'] = raw_text
        data['method'] = 'barcode'
        return data
    except Exception:
        return base_result
