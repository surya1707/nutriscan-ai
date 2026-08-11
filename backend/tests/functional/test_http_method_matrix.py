"""
Systematic HTTP method sweep: for every registered route, every method
NOT implemented for that route should return 405, not 404, not 500, and
not silently succeed. Built directly from the @router.get/post/patch/delete
decorators in app/routers/*.py and app/main.py.

Note: POST /history IS included in this sweep (it's not in IMPLEMENTED's
method set for "/history", so it's picked up as an "unimplemented" case
here) and correctly asserts today's real, current 405. That's a routing
contract check, not a comment on whether it SHOULD exist -- the business
case for why it should exist (the mobile app's offline-sync flow expects
it) is tracked separately as a strict-xfail in
tests/functional/test_history_functional.py, where it belongs.
"""
import pytest
from httpx import AsyncClient

ALL_METHODS = {"get", "post", "put", "patch", "delete"}

# route -> set of methods actually implemented
IMPLEMENTED = {
    "/": {"get"},
    "/health": {"get"},
    "/scan/analyse": {"post"},
    "/scan/barcode": {"post"},
    "/users/me": {"get", "patch", "delete"},
    "/history": {"get", "delete"},
    "/history/1": {"get", "delete"},
}

UNIMPLEMENTED_CASES = [
    (route, method)
    for route, implemented in IMPLEMENTED.items()
    for method in sorted(ALL_METHODS - implemented)
]


@pytest.mark.asyncio
@pytest.mark.parametrize("route,method", UNIMPLEMENTED_CASES, ids=[f"{m.upper()}_{r}" for r, m in UNIMPLEMENTED_CASES])
async def test_unimplemented_method_returns_405(auth_client: AsyncClient, route, method):
    """
    CATEGORY: Functional API
    TITLE: Every unimplemented (route, method) combination returns 405, not 404/500/2xx
    OBJECTIVE: Uses an authenticated client throughout (auth_client) so a
      405 is never confused with a 401 -- if a route required auth and
      returned 401 instead of 405 for a wrong-but-otherwise-valid method,
      that would mean method routing happens after auth instead of before,
      which is the wrong order for a clean API contract.
    SEVERITY: Low
    """
    response = await getattr(auth_client, method)(route)
    assert response.status_code == 405, (
        f"{method.upper()} {route} returned {response.status_code}, expected 405"
    )
