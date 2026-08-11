import pytest
import asyncio
import json
import base64
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.main import app
from app.core.database import Base, get_db
from app.core.deps import get_current_user_optional, get_current_user, security
from app.core.rate_limit import limiter

# Isolated in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Identity mocking
#
# [FIXTURE DESIGN NOTE - found by direct testing, not assumed] The original
# version of this fixture set overrode get_current_user_optional with a
# *static* lambda per client fixture (e.g. `lambda: mock_auth_user`). That
# works fine with exactly one authenticated client per test. It silently
# breaks the moment a test needs TWO simultaneously-active identities -- which
# every cross-tenant/IDOR test does by definition.
#
# Why: app.dependency_overrides is a single global dict on the shared `app`
# object. Pytest resolves ALL of a test's fixtures (both auth_client and
# auth_client_2) before the test body runs, so whichever fixture's setup runs
# last overwrites the override for BOTH clients for the rest of the test --
# regardless of which client variable a given request is made through.
# Confirmed empirically: every IDOR test using auth_client + auth_client_2
# together returned the second identity's data down both clients.
#
# Fix: install ONE override for the life of the test, and encode identity IN
# the request itself (each client's own default Authorization header),
# decoded fresh per-request. Two clients hitting the same `app` then resolve
# to two different identities correctly, no matter what order their fixtures
# were set up in.
# ---------------------------------------------------------------------------

_TEST_TOKEN_PREFIX = "TESTUSER:"
_TEST_TOKEN_NONE = _TEST_TOKEN_PREFIX + "NONE"


def _encode_identity_header(user_claims: dict | None) -> str:
    if not user_claims:
        return f"Bearer {_TEST_TOKEN_NONE}"
    payload = base64.urlsafe_b64encode(json.dumps(user_claims).encode()).decode()
    return f"Bearer {_TEST_TOKEN_PREFIX}{payload}"


def _decode_test_identity(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """
    Replaces get_current_user_optional for every fixture in this file. Reads
    the identity encoded in the *actual incoming request's* Authorization
    header rather than closing over fixture-setup-time state, so it works
    correctly no matter how many differently-identified clients are active
    in the same test.
    """
    if not credentials:
        return None
    token = credentials.credentials
    if not token.startswith(_TEST_TOKEN_PREFIX):
        return None
    payload = token[len(_TEST_TOKEN_PREFIX):]
    if payload == "NONE":
        return None
    try:
        return json.loads(base64.urlsafe_b64decode(payload.encode()).decode())
    except Exception:
        return None


def _install_identity_override(db: AsyncSession) -> None:
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _decode_test_identity
    # Let the REAL get_current_user run: it wraps get_current_user_optional
    # and raises 401 on a falsy value. Confirmed by direct testing that
    # FastAPI's override resolution is transitive, so this inherits our
    # override on get_current_user_optional automatically.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
async def async_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Unauthenticated client (no Authorization header -> anonymous)."""
    _install_identity_override(db)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
def mock_auth_user():
    return {"uid": "test_user_123", "email": "test@example.com"}


@pytest.fixture
async def auth_client(db: AsyncSession, mock_auth_user: dict) -> AsyncGenerator[AsyncClient, None]:
    _install_identity_override(db)

    transport = ASGITransport(app=app)
    headers = {"Authorization": _encode_identity_header(mock_auth_user)}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        yield client

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Additions below this line support the expanded functional/security/backend
# test suite (tests/functional, tests/security).
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_auth_user_2():
    """
    A second, distinct authenticated identity. Needed for cross-tenant / IDOR
    authorization tests: does identity A's token ever expose identity B's
    data? A single test account can only prove "logged in vs not logged in",
    never that.
    """
    return {"uid": "test_user_456_other_tenant", "email": "second-tenant@example.com"}


@pytest.fixture
async def auth_client_2(db: AsyncSession, mock_auth_user_2: dict) -> AsyncGenerator[AsyncClient, None]:
    """Authenticated client for the second identity. Safe to use alongside
    auth_client in the same test -- see the identity-mocking note above."""
    _install_identity_override(db)

    transport = ASGITransport(app=app)
    headers = {"Authorization": _encode_identity_header(mock_auth_user_2)}
    async with AsyncClient(transport=transport, base_url="http://test", headers=headers) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture
async def make_auth_client(db: AsyncSession):
    """
    Factory fixture for security tests that need to simulate malformed or
    edge-case decoded-token payloads (missing uid, empty uid, non-string uid,
    no email, etc.) without a real Firebase ID token.

    Usage:
        async def test_x(make_auth_client):
            client = await make_auth_client({"uid": "", "email": "a@b.com"})
            resp = await client.get("/users/me")

    Pass None (or {}) to simulate a token that fails verification entirely
    (current_user resolves to None, protected routes 401).
    """
    created_clients = []

    _install_identity_override(db)

    async def _factory(user_claims):
        transport = ASGITransport(app=app)
        headers = {"Authorization": _encode_identity_header(user_claims)}
        client = AsyncClient(transport=transport, base_url="http://test", headers=headers)
        created_clients.append(client)
        return client

    yield _factory

    for client in created_clients:
        await client.aclose()
    app.dependency_overrides.clear()


@pytest.fixture
async def raw_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Client with ONLY the DB dependency overridden. get_current_user /
    get_current_user_optional are left as the REAL implementation, so tests
    using this fixture exercise actual Authorization-header parsing and
    Firebase token verification -- not a test-only auth bypass.

    Under pytest, app/core/firebase.py never calls firebase_admin.initialize_app()
    (it short-circuits when "pytest" is in sys.modules), so there is no live
    Firebase project to verify a token against. Any token -- garbage, expired,
    forged, or a real one -- makes auth.verify_id_token() raise, which
    get_current_user_optional catches and turns into "unauthenticated". That
    means this fixture can prove invalid/missing/malformed tokens are
    correctly rejected (fails closed), but it CANNOT prove a genuinely valid
    token is accepted -- that needs a real Firebase project and is out of
    scope for CI. This gap is called out explicitly in the handover README.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    # Deliberately do NOT override get_current_user / get_current_user_optional.

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """
    [FINDING - confirmed by direct testing] slowapi's Limiter keeps its
    counters in a single process-wide in-memory store keyed by client IP.
    Every ASGITransport test client presents as the same host, so without
    this reset, whichever test happens to run first "spends" quota that
    every later test making the same call inherits -- order-dependent
    flakiness across the whole file, not just within one test.

    Confirmed: limiter.reset() reliably clears it. Runs before every test
    (autouse) so tests/security/test_rate_limiting.py can assert exact
    thresholds and every other test gets a full, unshared quota.
    """
    limiter.reset()
    yield


@pytest.fixture
async def crash_test_client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    [TEST-INFRA FINDING - confirmed by direct testing] httpx.ASGITransport
    defaults to raise_app_exceptions=True, which RE-RAISES any exception
    that escapes the app as a real Python exception in the test process,
    rather than delivering the HTTP response a real client would get.

    This app combines @app.middleware("http") (Starlette's BaseHTTPMiddleware
    pattern) with a global @app.exception_handler(Exception). Confirmed with
    a minimal reproduction against both a real uvicorn server AND
    ASGITransport: a real server correctly returns the sanitized 500 JSON
    body from global_exception_handler every time. The default
    ASGITransport(raise_app_exceptions=True) does NOT -- it re-raises the
    original exception into the test instead, which would make a naive
    "unhandled exceptions are sanitized" test fail for the wrong reason (it
    would look like the handler is broken, when actually only the test
    client is misconfigured for this scenario).

    Use THIS client -- not async_client/auth_client -- for any test that
    deliberately forces a route handler to raise, so the assertion reflects
    what a real client actually receives.
    """
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user_optional] = _decode_test_identity
    app.dependency_overrides.pop(get_current_user, None)

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
