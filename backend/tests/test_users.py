import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_get_profile_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/users/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_profile_authorized(auth_client: AsyncClient):
    response = await auth_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test_user_123"
    assert data["allergies"] == []

@pytest.mark.asyncio
async def test_patch_profile(auth_client: AsyncClient):
    # Ensure profile exists
    await auth_client.get("/users/me")
    
    payload = {"allergies": ["peanut"], "goals": ["weight loss"]}
    response = await auth_client.patch("/users/me", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "peanut" in data["allergies"]
    assert "weight loss" in data["goals"]

@pytest.mark.asyncio
async def test_delete_profile(auth_client: AsyncClient):
    # Ensure profile exists
    await auth_client.get("/users/me")
    
    response = await auth_client.delete("/users/me")
    assert response.status_code == 204
    
    # Try fetching again, it should re-create an empty profile
    response = await auth_client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["allergies"] == []
