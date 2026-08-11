"""
Functional API tests for /history, beyond the ownership/CRUD cases already
in tests/test_history.py.
"""
import pytest
from httpx import AsyncClient
from unittest.mock import patch


async def _create_n_history_items(auth_client: AsyncClient, n: int):
    for i in range(n):
        await auth_client.post("/scan/analyse", json={"ingredients": [f"item-{i}"]})


@pytest.mark.asyncio
async def test_history_pagination_limit(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: limit truncates results to the requested page size
    SEVERITY: Medium
    """
    await _create_n_history_items(auth_client, 5)
    response = await auth_client.get("/history", params={"limit": 2})
    assert response.status_code == 200
    assert len(response.json()) == 2


@pytest.mark.asyncio
async def test_history_pagination_offset(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: offset skips the newest N items (list is newest-first)
    SEVERITY: Medium
    """
    await _create_n_history_items(auth_client, 5)
    page1 = await auth_client.get("/history", params={"limit": 5, "offset": 0})
    page2 = await auth_client.get("/history", params={"limit": 5, "offset": 2})
    ids_page1 = [item["id"] for item in page1.json()]
    ids_page2 = [item["id"] for item in page2.json()]
    assert ids_page1[2:] == ids_page2[: len(ids_page1) - 2]


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason=(
        "[CONFIRMED BUG - found by this test, not assumed] routers/history.py "
        "orders by desc(ScanHistory.scanned_at), and models/history.py sets "
        "scanned_at via server_default=func.now(). Confirmed live: SQLite's "
        "CURRENT_TIMESTAMP has only SECOND granularity, so 3 scans made "
        "within the same second (normal for a user scanning several items "
        "in a row) all get an IDENTICAL scanned_at value. With no secondary "
        "sort key, ORDER BY on the tied column does not reliably return "
        "insertion order -- confirmed here it returns ascending id (oldest "
        "first) instead of the intended newest-first. A user who scans 3 "
        "products in quick succession sees them in the wrong order. "
        "REMEDIATION: add id DESC as a secondary sort key: "
        ".order_by(desc(ScanHistory.scanned_at), desc(ScanHistory.id))."
    ),
    strict=True,
)
async def test_history_ordered_newest_first(auth_client: AsyncClient):
    """
    CATEGORY: Functional API / Business Logic
    TITLE: [CONFIRMED BUG] History should be reliably ordered newest-first, even for scans made within the same second
    OBJECTIVE: Simulates the common case of a user scanning several products
      back-to-back (well within one second in an automated test, but this is
      also realistic for a fast human scanner or a barcode-gun-style flow).
    EXPECTED: ids returned in descending (newest-first) order.
    ACTUAL: ties on scanned_at fall back to ascending id (confirmed live).
    IMPACT: A user who scans several products in quick succession sees their
      history in the wrong order.
    REMEDIATION: add id DESC as a secondary sort key in routers/history.py:
      .order_by(desc(ScanHistory.scanned_at), desc(ScanHistory.id)).
    SEVERITY: Medium
    """
    await _create_n_history_items(auth_client, 3)
    response = await auth_client.get("/history")
    ids = [item["id"] for item in response.json()]
    assert ids == sorted(ids, reverse=True)


@pytest.mark.asyncio
@pytest.mark.parametrize("limit", [0, 101, -1])
async def test_history_limit_out_of_bounds_is_422(auth_client: AsyncClient, limit):
    """
    CATEGORY: Input Validation
    TITLE: limit outside [1, 100] (Query(20, ge=1, le=100)) is rejected
    SEVERITY: Medium
    """
    response = await auth_client.get("/history", params={"limit": limit})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_offset_negative_is_422(auth_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: A negative offset (Query(0, ge=0)) is rejected
    SEVERITY: Low
    """
    response = await auth_client.get("/history", params={"offset": -1})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_history_get_nonexistent_id_is_404(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Fetching a history id that was never created returns 404
    SEVERITY: Low
    """
    response = await auth_client.get("/history/999999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_history_get_non_numeric_id_is_422(auth_client: AsyncClient):
    """
    CATEGORY: Input Validation
    TITLE: A non-integer path id is rejected by FastAPI's path converter
    SEVERITY: Low
    """
    response = await auth_client.get("/history/not-a-number")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_clear_history_removes_everything(auth_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: DELETE /history (bulk clear) empties the list for that user
    SEVERITY: Medium
    """
    await _create_n_history_items(auth_client, 4)
    clear = await auth_client.delete("/history")
    assert clear.status_code == 204
    listing = await auth_client.get("/history")
    assert listing.json() == []


@pytest.mark.asyncio
@pytest.mark.xfail(
    reason=(
        "[KNOWN GAP - docs/AUDIT_REPORT.md 'Missing endpoint (contract gap)'] "
        "mobile/lib/services/api_service.dart:239 calls POST /history to push "
        "offline-created scans back to the server, but routers/history.py has "
        "no POST handler. Confirmed live: currently returns 405. This test "
        "encodes the CONTRACT THE MOBILE APP EXPECTS so it starts failing loudly "
        "(XPASS) the moment someone adds the route, as a reminder to remove "
        "this xfail marker rather than leave it stale."
    ),
    strict=True,
)
async def test_post_history_should_accept_offline_scan_sync(auth_client: AsyncClient):
    """
    CATEGORY: Functional API / Business Logic
    TITLE: [KNOWN GAP] POST /history should let the mobile app push an offline-created scan
    OBJECTIVE: Document the desired contract for the mobile offline-sync flow.
    EXPECTED: 201 with the created ScanHistoryResponse.
    ACTUAL: 405 Method Not Allowed (confirmed live) -- see xfail reason above for details.
    SEVERITY: Critical
    """
    payload = {
        "product_name": "Coca Cola",
        "brand": "Coca-Cola",
        "health_score": 25,
        "nova_group": 4,
        "nutrients": {"sugars": 10.6},
        "ingredients": ["Carbonated Water", "High Fructose Corn Syrup"],
    }
    response = await auth_client.post("/history", json=payload)
    assert response.status_code == 201
