"""
Security tests: configuration and HTTP headers (CORS, security headers,
API metadata exposure).
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_rejects_disallowed_origin(async_client: AsyncClient):
    """
    CATEGORY: Configuration / CORS
    TITLE: A preflight request from an origin not in ALLOWED_ORIGINS is rejected
    OBJECTIVE: Confirm CORSMiddleware is configured with an explicit allow-list
      (settings.ALLOWED_ORIGINS), not allow_origins=["*"].
    SEVERITY: High
    """
    response = await async_client.options(
        "/scan/analyse",
        headers={"Origin": "http://evil.example.com", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.asyncio
async def test_cors_accepts_configured_origin(async_client: AsyncClient):
    """
    CATEGORY: Configuration / CORS
    TITLE: A preflight request from an allow-listed origin succeeds and echoes that origin
    OBJECTIVE: Also confirms the allow-list is origin-specific (not "*") even
      when allow_credentials=true -- required, since browsers reject
      wildcard-origin + credentials combinations anyway, but worth locking in.
    SEVERITY: Medium
    """
    response = await async_client.options(
        "/scan/analyse",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-origin"] != "*"


@pytest.mark.asyncio
async def test_no_hardening_security_headers_present(async_client: AsyncClient):
    """
    CATEGORY: Configuration / Security Headers
    TITLE: [FINDING] No X-Content-Type-Options / X-Frame-Options / HSTS / CSP headers
    OBJECTIVE: Confirms the current, undocumented state of the response
      headers on a plain JSON API response.
    IMPACT: Low for a pure JSON API consumed by a known mobile/web client
      (there's no HTML rendering surface for clickjacking/MIME-sniffing to
      exploit directly here), but these are cheap, standard defense-in-depth
      headers and their absence should be a deliberate choice, not an
      oversight. HSTS in particular matters once this sits behind a public
      HTTPS endpoint (deploy notes mention Render, which terminates TLS at
      the edge -- confirm HSTS is added there or in this app).
    REMEDIATION: Add a small middleware (or starlette's SecurityHeaders
      pattern) setting X-Content-Type-Options: nosniff,
      X-Frame-Options: DENY, and Strict-Transport-Security in production.
    SEVERITY: Low
    """
    response = await async_client.get("/health")
    absent = [
        h
        for h in ("x-content-type-options", "x-frame-options", "strict-transport-security", "content-security-policy")
        if h in response.headers
    ]
    assert absent == [], f"Unexpectedly found hardening headers already present: {absent}"


@pytest.mark.asyncio
async def test_error_responses_are_valid_json_not_html(async_client: AsyncClient):
    """
    CATEGORY: Configuration
    TITLE: Every error path (404, 422, 429) returns application/json, never an HTML error page
    OBJECTIVE: A stray HTML error page is a common sign of an unhandled
      framework-level failure bypassing the app's own error handling.
    SEVERITY: Low
    """
    for response in (
        await async_client.get("/nonexistent-route"),
        await async_client.post("/scan/analyse", json={}),
    ):
        assert response.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_openapi_schema_is_reachable(async_client: AsyncClient):
    """
    CATEGORY: Configuration / Information Disclosure
    TITLE: [INFORMATIONAL] /docs and /openapi.json are exposed with default FastAPI settings
    OBJECTIVE: Document the current state -- FastAPI's interactive docs are
      not disabled (no docs_url=None / openapi_url=None in main.py's
      FastAPI(...) constructor).
    IMPACT: Informational only. A fully-documented schema of your own public
      API is not itself a vulnerability, but it does hand an attacker a
      complete endpoint/parameter map for free and should be a deliberate
      choice for a production deployment, not a default left over from
      development.
    SEVERITY: Informational
    """
    docs = await async_client.get("/docs")
    schema = await async_client.get("/openapi.json")
    assert docs.status_code == 200
    assert schema.status_code == 200


@pytest.mark.asyncio
async def test_server_header_does_not_leak_detailed_version_info(async_client: AsyncClient):
    """
    CATEGORY: Configuration / Information Disclosure
    TITLE: The Server response header (if present) doesn't reveal a specific framework/OS version
    SEVERITY: Informational
    """
    response = await async_client.get("/health")
    server_header = response.headers.get("server", "")
    # A bare "uvicorn" (or absent) is fine; a full "uvicorn/0.27.1 (Ubuntu 22.04)"-style
    # string is the kind of thing worth stripping at the reverse proxy in production.
    assert "/" not in server_header
