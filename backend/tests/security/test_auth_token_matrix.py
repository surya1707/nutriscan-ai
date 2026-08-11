"""
Comprehensive matrix: every kind of invalid Authorization header we can
throw at it, times every protected endpoint. Complements
tests/security/test_authentication.py's individual, narrative tests (which
explain WHY each token type matters) with a flat, exhaustive sweep that
catches a regression on any single (token_type, endpoint) cell.

Uses raw_client (see conftest.py) throughout -- real header parsing and
real Firebase token verification, not a test-only bypass. Every token
type below was manually confirmed to be transportable as a real HTTP
header (httpx itself refuses to send raw non-ASCII bytes in a header,
which ruled out a literal-unicode-emoji case -- that's not a gap in this
suite, it's not a real reachable scenario over actual HTTP).
"""
import jwt
import pytest
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

_FORGED_ALG_NONE = jwt.encode({"uid": "attacker"}, key="", algorithm="none")


def _forged_hs256():
    # Signed with a plausible-but-wrong app secret, not the real one -- the
    # point is confirming ANY locally-guessable secret is rejected, since
    # Firebase ID tokens are RS256 and this app has no HS256 issuance path.
    return jwt.encode({"uid": "attacker"}, key="guessed-secret-not-the-real-one", algorithm="HS256")


TOKEN_TYPES = {
    "empty": "",
    "garbage-string": "not-a-real-jwt-at-all",
    "sqli-string": "' OR '1'='1",
    "jwt-alg-none-forged": _FORGED_ALG_NONE,
    "jwt-hs256-guessed-secret": _forged_hs256(),
    "oversized-50k-chars": "a" * 50_000,
    "null-byte-containing": "abc\x00def",
    "whitespace-only": "   ",
    "duplicate-bearer-prefix": "Bearer sometoken",  # -> header becomes "Bearer Bearer sometoken"
    "valid-jwt-structure-garbage-signature": (
        "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJ1aWQiOiJhdHRhY2tlciJ9."
        "garbagesignaturenotreal"
    ),
    "crlf-injection-attempt": "abc\r\nX-Injected-Header: true",
}


def _matrix_ids():
    return [f"{t}__{m.upper()}_{p}" for t in TOKEN_TYPES for m, p in PROTECTED_ENDPOINTS]


def _matrix_cases():
    return [(t, m, p) for t in TOKEN_TYPES for m, p in PROTECTED_ENDPOINTS]


@pytest.mark.asyncio
@pytest.mark.parametrize("token_type,method,path", _matrix_cases(), ids=_matrix_ids())
async def test_invalid_token_type_rejected_on_every_protected_endpoint(
    raw_client: AsyncClient, token_type, method, path
):
    """
    CATEGORY: Authentication
    TITLE: Every invalid-token type is rejected (401) on every protected endpoint
    OBJECTIVE: 11 token types x 7 endpoints = 77 real, independently
      meaningful checks -- confirms no single endpoint has a gap in its
      auth dependency wiring that would only show up for one specific kind
      of bad token.
    SEVERITY: Critical
    """
    token_value = TOKEN_TYPES[token_type]
    response = await getattr(raw_client, method)(path, headers={"Authorization": f"Bearer {token_value}"})
    assert response.status_code == 401, (
        f"token_type={token_type!r} on {method.upper()} {path} returned "
        f"{response.status_code}, expected 401"
    )
