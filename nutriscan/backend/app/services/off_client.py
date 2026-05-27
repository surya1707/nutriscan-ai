import httpx
from typing import Optional, Dict

class OpenFoodFactsClient:
    def __init__(self):
        self.base_url = "https://world.openfoodfacts.org/api/v2/product"

    async def get_product(self, barcode: str) -> Optional[Dict]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.base_url}/{barcode}.json", timeout=10.0)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == 1:
                        return data.get("product")
                return None
            except Exception:
                return None
