import httpx
from typing import Optional, Dict
from ..core.cache import cache

class OpenFoodFactsClient:
    def __init__(self):
        self.base_url = "https://world.openfoodfacts.org/api/v2/product"

    async def get_product(self, barcode: str) -> Optional[Dict]:
        cache_key = f"off_product:{barcode}"
        
        # Try cache first
        cached_product = await cache.get_json(cache_key)
        if cached_product:
            return cached_product
            
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/{barcode}.json", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1:
                        product = data.get("product")
                        # Store in cache (fails open on error internally)
                        await cache.set_json(cache_key, product)
                        return product
                return None
            except Exception:
                return None
