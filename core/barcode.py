import requests

_OFF_URL = "https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
_TIMEOUT = 10


def lookup_barcode(barcode: str) -> dict | None:
    """Fetch product nutrition from OpenFoodFacts. Returns normalized dict or None."""
    barcode = barcode.strip()
    if not barcode.isdigit():
        return None

    try:
        resp = requests.get(
            _OFF_URL.format(barcode=barcode),
            timeout=_TIMEOUT,
            headers={"User-Agent": "NutriLens/1.0"},
        )
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None

    if data.get("status") != 1:
        return None

    product = data.get("product", {})
    nutr = product.get("nutriments", {})

    name = (
        product.get("product_name")
        or product.get("generic_name")
        or "Unknown Product"
    )

    # Normalize per 100 g
    calories = int(nutr.get("energy-kcal_100g", 0))
    carbs = round(float(nutr.get("carbohydrates_100g", 0)), 1)
    protein = round(float(nutr.get("proteins_100g", 0)), 1)
    fat = round(float(nutr.get("fat_100g", 0)), 1)

    serving_g = _parse_serving(product)

    return {
        "name": name,
        "brand": product.get("brands", ""),
        "image_url": product.get("image_front_small_url", ""),
        "calories_100g": calories,
        "carbs_100g": carbs,
        "protein_100g": protein,
        "fat_100g": fat,
        "serving_g": serving_g,
        "barcode": barcode,
    }


def _parse_serving(product: dict) -> int:
    """Try to extract a numeric serving size in grams."""
    qty = product.get("serving_quantity")
    if qty:
        try:
            return int(float(qty))
        except (ValueError, TypeError):
            pass
    return 100
