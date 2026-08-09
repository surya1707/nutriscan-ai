import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_analyse_ingredients_happy_path(async_client: AsyncClient):
    payload = {"ingredients": ["water", "salt"]}
    response = await async_client.post("/scan/analyse", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["ingredients"]) == 2
    assert data["safety_score"] > 0
    assert data["nova_class"] > 0
    assert "breakdown" in data

@pytest.mark.asyncio
async def test_analyse_ingredients_empty(async_client: AsyncClient):
    payload = {"ingredients": []}
    response = await async_client.post("/scan/analyse", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["ingredients"]) == 0
    assert data["safety_score"] == 100
    assert data["nova_class"] == 1

@pytest.mark.asyncio
@patch("app.routers.scan.off_client.get_product")
async def test_analyse_barcode_not_found(mock_get_product, async_client: AsyncClient):
    mock_get_product.return_value = None
    
    payload = {"barcode": "123456789"}
    response = await async_client.post("/scan/barcode", json=payload)
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found in database"
