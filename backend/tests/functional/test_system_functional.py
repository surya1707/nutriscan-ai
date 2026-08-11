"""
Functional API tests: system-level endpoints (/, /health) and the generic
HTTP contract (404 for unknown routes, 405 for wrong methods) that every
other test file implicitly relies on.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint_shape(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Root endpoint returns a stable status payload
    OBJECTIVE: Confirm GET / never regresses to a 500 or a missing key.
    EXPECTED: 200 with "message" and "status" keys.
    SEVERITY: Low
    """
    response = await async_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["status"] == "online"


@pytest.mark.asyncio
async def test_health_endpoint_reports_all_subsystems(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: /health reports db, redis, and environment
    OBJECTIVE: Confirm the readiness probe contract used by Docker/CI healthchecks.
    EXPECTED: 200 (even when a dependency is degraded -- see docker-compose.yml
      healthcheck, which polls this endpoint) with db/redis/environment keys.
    SEVERITY: Medium
    """
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert set(["status", "db", "redis", "environment"]).issubset(data.keys())
    assert data["status"] in ("ok", "degraded")
    # DB must be reachable in the CI/ephemeral SQLite setup this suite runs against.
    assert data["db"] == "ok"


@pytest.mark.asyncio
async def test_unknown_route_returns_404(async_client: AsyncClient):
    """
    CATEGORY: Functional API
    TITLE: Unknown route returns 404, not a stack trace
    SEVERITY: Low
    """
    response = await async_client.get("/this/route/does/not/exist")
    assert response.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/health"),
        ("delete", "/health"),
        ("put", "/"),
        ("post", "/"),
    ],
)
async def test_wrong_method_returns_405(async_client: AsyncClient, method, path):
    """
    CATEGORY: Functional API
    TITLE: Unsupported HTTP method on a known route returns 405
    OBJECTIVE: FastAPI's default routing must reject wrong verbs cleanly,
      not fall through to an unrelated handler.
    SEVERITY: Low
    """
    response = await getattr(async_client, method)(path)
    assert response.status_code == 405


@pytest.mark.asyncio
async def test_global_exception_handler_hides_internals(crash_test_client: AsyncClient, monkeypatch):
    """
    CATEGORY: Configuration / Error Handling
    TITLE: Unhandled exceptions never leak internals to the client
    OBJECTIVE: app/main.py registers a catch-all exception handler
      (global_exception_handler). Force a downstream failure and confirm the
      client only ever sees the generic {"error": ..., "detail": ...} shape,
      never a Python traceback, file path, or exception message.

      NOTE: uses crash_test_client (raise_app_exceptions=False), confirmed
      by direct testing to be necessary here -- the default test clients'
      ASGITransport re-raises escaped exceptions into the test process
      instead of returning the response a real client gets. Verified against
      both a real uvicorn server and ASGITransport directly: production
      returns the sanitized body correctly; only the default test-client
      config would (incorrectly) look like the handler had failed.
    EXPECTED: 500 with the generic sanitized body.
    SEVERITY: High
    """
    from app.routers import scan as scan_router

    def _boom(*args, **kwargs):
        raise RuntimeError("SECRET_INTERNAL_DETAIL_should_never_reach_the_client")

    monkeypatch.setattr(scan_router.engine, "analyze_ingredients", _boom)

    response = await crash_test_client.post("/scan/analyse", json={"ingredients": ["water"]})
    assert response.status_code == 500
    data = response.json()
    assert data == {"error": "Internal Server Error", "detail": "An unexpected error occurred."}
    assert "SECRET_INTERNAL_DETAIL_should_never_reach_the_client" not in response.text
    assert "Traceback" not in response.text
