"""
Security tests: authorization / IDOR (Insecure Direct Object Reference).

Every test here uses TWO distinct, fully-authenticated identities
(auth_client / auth_client_2, see conftest.py) so we're proving "user A
cannot touch user B's data", not just "logged in vs not logged in". A
single test account can never catch a cross-tenant leak.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_cannot_list_another_users_history(auth_client: AsyncClient, auth_client_2: AsyncClient):
    """
    CATEGORY: Authorization / IDOR
    TITLE: GET /history never returns another identity's scans
    SEVERITY: Critical
    """
    await auth_client_2.post("/scan/analyse", json={"ingredients": ["water"]})  # user 2 creates data

    response = await auth_client.get("/history")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_user_cannot_fetch_another_users_history_item_by_id(
    auth_client: AsyncClient, auth_client_2: AsyncClient
):
    """
    CATEGORY: Authorization / IDOR
    TITLE: GET /history/{id} 404s for an id owned by a different identity
    OBJECTIVE: Confirm this is a real 404 (ownership-checked), not a 403 that
      would leak "this id exists, just isn't yours" -- get_scan_or_404()
      filters by id AND user_id in a single query, so a non-owner sees the
      exact same response as a nonexistent id.
    SEVERITY: Critical
    """
    create = await auth_client_2.post("/scan/analyse", json={"ingredients": ["water"]})
    other_id = (await auth_client_2.get("/history")).json()[0]["id"]
    assert create.status_code == 200

    response = await auth_client.get(f"/history/{other_id}")
    assert response.status_code == 404

    not_found = await auth_client.get("/history/999999999")
    assert response.status_code == not_found.status_code  # same shape as truly-nonexistent


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_history_item(
    auth_client: AsyncClient, auth_client_2: AsyncClient
):
    """
    CATEGORY: Authorization / IDOR
    TITLE: DELETE /history/{id} cannot delete another identity's item
    SEVERITY: Critical
    """
    await auth_client_2.post("/scan/analyse", json={"ingredients": ["water"]})
    other_id = (await auth_client_2.get("/history")).json()[0]["id"]

    delete_attempt = await auth_client.delete(f"/history/{other_id}")
    assert delete_attempt.status_code == 404

    still_there = await auth_client_2.get(f"/history/{other_id}")
    assert still_there.status_code == 200


@pytest.mark.asyncio
async def test_bulk_clear_history_only_affects_caller(auth_client: AsyncClient, auth_client_2: AsyncClient):
    """
    CATEGORY: Authorization / IDOR
    TITLE: DELETE /history (bulk clear) is scoped to the caller only
    OBJECTIVE: clear_history() does `WHERE user_id == current_user["uid"]`.
      A missing WHERE clause here would wipe every user's history.
    SEVERITY: Critical
    """
    await auth_client.post("/scan/analyse", json={"ingredients": ["water"]})
    await auth_client_2.post("/scan/analyse", json={"ingredients": ["water"]})

    await auth_client.delete("/history")

    mine = await auth_client.get("/history")
    theirs = await auth_client_2.get("/history")
    assert mine.json() == []
    assert len(theirs.json()) == 1


@pytest.mark.asyncio
async def test_users_do_not_see_each_others_profile_fields(
    auth_client: AsyncClient, auth_client_2: AsyncClient
):
    """
    CATEGORY: Authorization / IDOR
    TITLE: Each identity's GET /users/me only ever reflects its own profile
    SEVERITY: Critical
    """
    await auth_client.get("/users/me")
    await auth_client.patch("/users/me", json={"allergies": ["shellfish"], "display_name": "User One"})

    await auth_client_2.get("/users/me")
    await auth_client_2.patch("/users/me", json={"allergies": ["gluten"], "display_name": "User Two"})

    profile_1 = (await auth_client.get("/users/me")).json()
    profile_2 = (await auth_client_2.get("/users/me")).json()

    assert profile_1["id"] != profile_2["id"]
    assert profile_1["allergies"] == ["shellfish"]
    assert profile_2["allergies"] == ["gluten"]
    assert profile_1["display_name"] == "User One"
    assert profile_2["display_name"] == "User Two"


@pytest.mark.asyncio
async def test_deleting_own_profile_does_not_touch_other_users_data(
    auth_client: AsyncClient, auth_client_2: AsyncClient
):
    """
    CATEGORY: Authorization / IDOR
    TITLE: DELETE /users/me only cascades within the caller's own data
    OBJECTIVE: delete_my_profile() cascades to ScanHistory filtered by the
      caller's own uid. Confirm a second identity's profile and history
      survive completely untouched.
    SEVERITY: Critical
    """
    await auth_client.get("/users/me")
    await auth_client_2.get("/users/me")
    await auth_client_2.post("/scan/analyse", json={"ingredients": ["water"]})

    delete = await auth_client.delete("/users/me")
    assert delete.status_code == 204

    other_profile = await auth_client_2.get("/users/me")
    other_history = await auth_client_2.get("/history")
    assert other_profile.status_code == 200
    assert len(other_history.json()) == 1


@pytest.mark.asyncio
async def test_history_id_enumeration_across_owners_always_404s_for_non_owner(
    auth_client: AsyncClient, auth_client_2: AsyncClient
):
    """
    CATEGORY: Authorization / IDOR
    TITLE: Sweeping a range of ids that DO exist (owned by someone else) never
      succeeds for a non-owner, even by chance
    OBJECTIVE: Simulates an attacker enumerating small sequential integer ids
      (auto-increment primary key) hoping to hit someone else's record.
    SEVERITY: Critical
    """
    for _ in range(5):
        await auth_client_2.post("/scan/analyse", json={"ingredients": ["water"]})
    existing_ids = [item["id"] for item in (await auth_client_2.get("/history")).json()]
    assert len(existing_ids) == 5

    for existing_id in existing_ids:
        response = await auth_client.get(f"/history/{existing_id}")
        assert response.status_code == 404, f"id {existing_id} leaked across tenants"
