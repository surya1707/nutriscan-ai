"""
Functional API tests for /users/me, beyond the happy-path cases already in
tests/test_users.py.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_patch_partial_update_preserves_other_fields(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: PATCH only updates the fields sent, leaving others untouched
    OBJECTIVE: UserProfileUpdateRequest fields are all Optional; the router
      does `.model_dump(exclude_unset=True)`. Confirm a PATCH with only
      "goals" does not clobber a previously-set "allergies" list.
    SEVERITY: High
    """
    await auth_client.get("/users/me")
    await auth_client.patch("/users/me", json={"allergies": ["peanut"]})

    response = await auth_client.patch("/users/me", json={"goals": ["weight loss"]})
    assert response.status_code == 200
    data = response.json()
    assert data["allergies"] == ["peanut"]
    assert data["goals"] == ["weight loss"]


@pytest.mark.asyncio
async def test_patch_empty_body_is_a_no_op(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: PATCH with an empty JSON body changes nothing and still returns 200
    SEVERITY: Low
    """
    await auth_client.get("/users/me")
    await auth_client.patch("/users/me", json={"allergies": ["dairy"]})

    response = await auth_client.patch("/users/me", json={})
    assert response.status_code == 200
    assert response.json()["allergies"] == ["dairy"]


@pytest.mark.asyncio
async def test_patch_invalid_type_for_allergies_is_422(auth_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: PATCH rejects a non-list value for a list field
    SEVERITY: Medium
    """
    await auth_client.get("/users/me")
    response = await auth_client.patch("/users/me", json={"allergies": "peanut"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_profile_is_idempotent_auto_create(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Calling GET /users/me twice does not error or duplicate the row
    OBJECTIVE: The auto-create-on-first-access path uses id as primary key,
      so a second GET should hit the SELECT branch, not attempt a second INSERT.
    SEVERITY: Medium
    """
    first = await auth_client.get("/users/me")
    second = await auth_client.get("/users/me")
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_patch_after_delete_returns_404_not_auto_create(auth_client: AsyncClient):
    """
    CATEGORY: Functional API / Business Logic
    TITLE: PATCH does not auto-create a profile the way GET does
    OBJECTIVE: update_my_profile() raises 404 if no row exists -- unlike
      get_my_profile(), it has no auto-create branch. Confirm that contract
      holds after a real delete.
    SEVERITY: Medium
    """
    await auth_client.get("/users/me")
    await auth_client.delete("/users/me")

    response = await auth_client.patch("/users/me", json={"goals": ["muscle gain"]})
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unsupported_method_on_users_me(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: PUT (unsupported verb) on /users/me returns 405
    SEVERITY: Low
    """
    response = await auth_client.put("/users/me", json={})
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_display_name_round_trips(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: display_name set via PATCH is returned verbatim by GET
    SEVERITY: Low
    """
    await auth_client.get("/users/me")
    await auth_client.patch("/users/me", json={"display_name": "Priya S."})
    response = await auth_client.get("/users/me")
    assert response.json()["display_name"] == "Priya S."
