"""
Security tests: rate limiting.

routers/scan.py applies @limiter.limit("30/minute") to POST /scan/analyse
and POST /scan/barcode independently. The _reset_rate_limiter autouse
fixture in conftest.py guarantees each test starts with a full, unshared
quota (see conftest.py docstring for why that reset is necessary).
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_scan_analyse_allows_exactly_30_requests_per_minute(async_client: AsyncClient):
    """
    CATEGORY: Rate Limiting / DAST
    TITLE: POST /scan/analyse permits exactly the documented 30 requests, then blocks
    SEVERITY: High
    """
    statuses = []
    for _ in range(30):
        response = await async_client.post("/scan/analyse", json={"ingredients": ["water"]})
        statuses.append(response.status_code)
    assert all(code == 200 for code in statuses), statuses


@pytest.mark.asyncio
async def test_scan_analyse_31st_request_in_window_is_429(async_client: AsyncClient):
    """
    CATEGORY: Rate Limiting / DAST
    TITLE: The 31st request within the same minute is rejected with 429
    SEVERITY: High
    """
    for _ in range(30):
        await async_client.post("/scan/analyse", json={"ingredients": ["water"]})

    response = await async_client.post("/scan/analyse", json={"ingredients": ["water"]})
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json()["error"]


@pytest.mark.asyncio
async def test_rate_limit_does_not_block_a_completely_unrelated_request_body(async_client: AsyncClient):
    """
    CATEGORY: Rate Limiting
    TITLE: The limiter keys on client identity + route, not on request content
    OBJECTIVE: Confirm varying the ingredients payload doesn't let a client
      dodge the limit (i.e. the limiter isn't accidentally keyed on a hash
      of the body, which would make it trivially bypassable).
    SEVERITY: Medium
    """
    for i in range(30):
        await async_client.post("/scan/analyse", json={"ingredients": [f"unique-ingredient-{i}"]})

    response = await async_client.post("/scan/analyse", json={"ingredients": ["yet-another-unique-one"]})
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_scan_analyse_and_scan_barcode_have_independent_buckets(async_client: AsyncClient):
    """
    CATEGORY: Rate Limiting
    TITLE: Exhausting /scan/analyse's quota does not affect /scan/barcode
    OBJECTIVE: Each @limiter.limit(...) decorator is evaluated per-route.
      Confirm that's actually true end-to-end, not just true by code
      inspection -- a shared global bucket would be a functional regression.
    SEVERITY: Medium
    """
    for _ in range(30):
        await async_client.post("/scan/analyse", json={"ingredients": ["water"]})
    exhausted = await async_client.post("/scan/analyse", json={"ingredients": ["water"]})
    assert exhausted.status_code == 429

    still_available = await async_client.post("/scan/barcode", json={"barcode": "0000000000000"})
    assert still_available.status_code != 429


@pytest.mark.asyncio
async def test_authenticated_endpoints_have_no_rate_limit_configured(auth_client: AsyncClient):
    """
    CATEGORY: Rate Limiting / Configuration
    TITLE: [FINDING] /users/me and /history have no @limiter.limit(...) at all
    OBJECTIVE: main.py only wires the limiter's exception handler and state;
      routers/user.py and routers/history.py never import or apply @limiter.
      This test demonstrates the current (unlimited) behavior explicitly
      rather than leaving it undocumented.
    IMPACT: Low -- both routers require a valid authenticated identity via
      get_current_user, so this isn't an anonymous-abuse vector the way an
      unlimited /scan/analyse would be. Still worth tracking: a compromised
      or leaked token currently has no throttle on read/write volume against
      a user's own data (e.g. scripted DELETE-then-recreate loops, or bulk
      history scraping).
    REMEDIATION: Consider a generous per-user rate limit (e.g. 120/minute)
      on authenticated routes as defense in depth, matching the pattern
      already established for /scan/*.
    SEVERITY: Low
    """
    statuses = []
    for _ in range(50):
        response = await auth_client.get("/users/me")
        statuses.append(response.status_code)
    assert all(code == 200 for code in statuses)
    assert 429 not in statuses  # documents current behavior; not a pass/fail security gate
