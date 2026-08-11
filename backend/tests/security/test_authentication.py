"""
Security tests: authentication.

These use raw_client (see conftest.py), which leaves get_current_user /
get_current_user_optional as the REAL implementation, so every test here
exercises actual Authorization-header parsing and Firebase token
verification -- not a test-only bypass.

KNOWN LIMIT (documented, not hidden): under pytest there is no live Firebase
project, so auth.verify_id_token() can never succeed here -- every token,
valid or not, is rejected. That means this file proves the fail-closed
direction (bad tokens -> always 401) exhaustively, but cannot prove a
genuinely valid token is accepted. See handover README "Known testing gaps".
"""
import pytest
import jwt
from httpx import AsyncClient

PROTECTED_ENDPOINTS = [
    ("get", "/users/me"),
    ("patch", "/users/me"),
    ("delete", "/users/me"),
    ("get", "/history"),
    ("get", "/history/1"),
    ("delete", "/history/1"),
    ("delete", "/history"),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
async def test_no_auth_header_rejected_on_every_protected_endpoint(raw_client: AsyncClient, method, path):
    """
    CATEGORY: Authentication
    TITLE: Every protected endpoint rejects requests with no Authorization header
    OBJECTIVE: Sweep all get_current_user-gated routes, not just one sample.
    SEVERITY: Critical
    """
    response = await getattr(raw_client, method)(path)
    assert response.status_code == 401


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
async def test_garbage_bearer_token_rejected_on_every_protected_endpoint(raw_client: AsyncClient, method, path):
    """
    CATEGORY: Authentication
    TITLE: A syntactically-invalid bearer token is rejected on every protected endpoint
    SEVERITY: Critical
    """
    response = await getattr(raw_client, method)(
        path, headers={"Authorization": "Bearer not-a-real-jwt-at-all"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_empty_bearer_token_rejected(raw_client: AsyncClient):
    """
    CATEGORY: Authentication
    TITLE: "Bearer " with no token value is rejected
    SEVERITY: High
    """
    response = await raw_client.get("/users/me", headers={"Authorization": "Bearer "})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_non_bearer_auth_scheme_rejected(raw_client: AsyncClient):
    """
    CATEGORY: Authentication
    TITLE: A non-Bearer auth scheme (e.g. Basic) is rejected, not silently accepted
    OBJECTIVE: HTTPBearer(auto_error=False) should refuse to extract credentials
      from a differently-schemed header, leaving current_user falsy -> 401.
    SEVERITY: High
    """
    response = await raw_client.get("/users/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_sql_injection_style_string_as_token_rejected(raw_client: AsyncClient):
    """
    CATEGORY: Authentication / Injection
    TITLE: A SQLi-style payload used as the bearer token is rejected, not specially parsed
    OBJECTIVE: Confirm the token value is only ever passed to
      firebase_admin.auth.verify_id_token() (which will reject it as a
      malformed JWT) and never reaches a raw SQL string anywhere.
    SEVERITY: High
    """
    response = await raw_client.get("/users/me", headers={"Authorization": "Bearer ' OR '1'='1"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forged_alg_none_jwt_rejected(raw_client: AsyncClient):
    """
    CATEGORY: Authentication
    TITLE: A self-signed / "alg: none" forged JWT asserting an arbitrary uid is rejected
    OBJECTIVE: Classic JWT-library vulnerability class: an attacker crafts a
      token with alg=none (or an unsigned/garbage signature) claiming any uid
      they like. Confirms the app relies on Firebase's real signature
      verification (auth.verify_id_token) rather than a naive decode.
    SEVERITY: Critical
    """
    forged = jwt.encode({"uid": "attacker", "email": "attacker@example.com"}, key="", algorithm="none")
    response = await raw_client.get("/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or missing authentication token"


@pytest.mark.asyncio
async def test_forged_hs256_jwt_with_guessed_secret_rejected(raw_client: AsyncClient):
    """
    CATEGORY: Authentication
    TITLE: A JWT signed with the app's own SECRET_KEY (HS256) is still rejected
    OBJECTIVE: Firebase ID tokens are RS256, signed by Google -- the app's
      local SECRET_KEY (used elsewhere, e.g. for anything HS256-based) must
      NOT be a valid signing key for auth tokens. This guards against an
      algorithm-confusion attack where an attacker signs a token with a
      secret they can guess or find (e.g. a leaked .env).
    SEVERITY: Critical
    """
    from app.core.config import settings

    forged = jwt.encode(
        {"uid": "attacker", "email": "attacker@example.com"},
        key=settings.SECRET_KEY,
        algorithm="HS256",
    )
    response = await raw_client.get("/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_malformed_token_on_optional_auth_endpoint_degrades_to_anonymous(raw_client: AsyncClient):
    """
    CATEGORY: Authentication
    TITLE: A malformed token on an optional-auth endpoint never causes a 500
    OBJECTIVE: /scan/analyse uses get_current_user_optional, which must
      swallow verification errors and degrade to "anonymous", not propagate
      an exception.
    EXPECTED: 200 (treated as anonymous), never 401 or 500.
    SEVERITY: High
    """
    response = await raw_client.post(
        "/scan/analyse",
        json={"ingredients": ["water"]},
        headers={"Authorization": "Bearer totally-invalid"},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_oversized_token_does_not_crash_server(raw_client: AsyncClient):
    """
    CATEGORY: Authentication / Input Validation
    TITLE: An extremely long bearer token value is rejected cleanly, not a 500
    SEVERITY: Medium
    """
    huge_token = "a" * 50_000
    response = await raw_client.get("/users/me", headers={"Authorization": f"Bearer {huge_token}"})
    assert response.status_code == 401
