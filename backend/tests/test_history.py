import pytest
from httpx import AsyncClient
from app.models.history import ScanHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

@pytest.mark.asyncio
async def test_list_history_empty(auth_client: AsyncClient):
    response = await auth_client.get("/history")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_history_via_scan_and_list(auth_client: AsyncClient):
    # Ensure profile exists for the user
    await auth_client.get("/users/me")

    # Trigger a scan to create history
    payload = {"ingredients": ["water", "salt"]}
    scan_response = await auth_client.post("/scan/analyse", json=payload)
    assert scan_response.status_code == 200

    # Check history
    response = await auth_client.get("/history")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["product_name"] == "Custom Scan"
    
    # Check single item
    item_id = data[0]["id"]
    single_res = await auth_client.get(f"/history/{item_id}")
    assert single_res.status_code == 200
    assert single_res.json()["id"] == item_id
    
    # Delete single item
    del_res = await auth_client.delete(f"/history/{item_id}")
    assert del_res.status_code == 204
    
    # Verify deletion
    verify_res = await auth_client.get(f"/history/{item_id}")
    assert verify_res.status_code == 404

@pytest.mark.asyncio
async def test_history_ownership(auth_client: AsyncClient, db: AsyncSession):
    # Create a history item for ANOTHER user directly in DB
    other_item = ScanHistory(
        user_id="other_user_456",
        product_name="Other Product",
        health_score=50,
        nova_group=3
    )
    db.add(other_item)
    await db.commit()
    await db.refresh(other_item)
    
    # auth_client is test_user_123, should not see other_user_456's history
    response = await auth_client.get("/history")
    assert response.status_code == 200
    # Make sure it doesn't contain the other item
    assert not any(item["id"] == other_item.id for item in response.json())
    
    # Try to access by ID
    single_res = await auth_client.get(f"/history/{other_item.id}")
    assert single_res.status_code == 404
    
    # Try to delete by ID
    del_res = await auth_client.delete(f"/history/{other_item.id}")
    assert del_res.status_code == 404
