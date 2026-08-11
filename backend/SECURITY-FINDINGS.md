# Backend Test Findings — nutriscan-ai

All findings below were **confirmed by direct testing** against the real
application (not inferred from reading code), and each one has a
corresponding regression test in `tests/` so it can't silently regress or
silently get "fixed" without anyone noticing. The machine-readable version
of this table is `tests/reporting/output/findings.xlsx` (regenerate with
`python tests/reporting/generate_reports.py`).

## Application findings

| Severity | Finding | Where | Regression test |
|---|---|---|---|
| Critical | `POST /history` doesn't exist (405) even though the mobile app's offline-sync flow expects it — matches the gap already flagged in `docs/AUDIT_REPORT.md` | `app/routers/history.py` | `tests/functional/test_history_functional.py::test_post_history_should_accept_offline_scan_sync` (strict xfail — will loudly XPASS-fail once someone adds the route, as a reminder to remove the marker) |
| Medium | History ordering is not reliably newest-first: `scanned_at` uses `server_default=func.now()`, and SQLite's `CURRENT_TIMESTAMP` only has **second** granularity. Several scans within the same second (normal for a fast scanner or automated flow) tie on `scanned_at`, and with no secondary sort key the tie-break is not what a user would expect. **Fix:** add `id DESC` as a secondary sort key: `.order_by(desc(ScanHistory.scanned_at), desc(ScanHistory.id))` | `app/routers/history.py` line ~48 | `tests/functional/test_history_functional.py::test_history_ordered_newest_first` (strict xfail) |
| Medium | `BarcodeRequest.barcode` has no format/character validation. Confirmed live: a barcode of `"../../../etc/passwd"` produces the literal outbound request `.../api/v2/product/../../../etc/passwd.json` — the value is f-string-concatenated into the OFF API URL, not `urljoin`'d or validated. Low impact today (the host is hardcoded), but exactly the shape that becomes exploitable if this pattern is ever reused or the base URL becomes configurable. **Fix:** constrain `barcode` to a numeric EAN/UPC pattern (8–14 digits) in the Pydantic schema | `app/schemas/scan.py`, `app/services/off_client.py` | `tests/security/test_input_validation_injection.py::test_barcode_value_reaches_outbound_url_unsanitized` |
| Low | No hardening headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, CSP) on any response | `app/main.py` | `tests/security/test_configuration_headers.py::test_no_hardening_security_headers_present` |
| Low | `/users/me` and `/history` have no rate limit at all (only `/scan/*` does). Low risk since both require a valid authenticated identity, but a compromised/leaked token currently has no throttle | `app/routers/user.py`, `app/routers/history.py` | `tests/security/test_rate_limiting.py::test_authenticated_endpoints_have_no_rate_limit_configured` |
| Informational | `/docs` and `/openapi.json` are exposed with FastAPI's defaults — hands out a full endpoint/parameter map for free. Worth a deliberate choice for production, not a leftover default | `app/main.py` (`FastAPI(...)` constructor) | `tests/security/test_configuration_headers.py::test_openapi_schema_is_reachable` |

## Things checked and confirmed **not** to be a problem

Worth recording explicitly — a passing test here is doing real work, not
just padding a count:

- **SQL injection**: SQLAlchemy's ORM parameterizes everything; injection-style strings in ingredient names, allergy lists, and display names are stored/returned as inert data (`tests/security/test_input_validation_injection.py`).
- **JWT forgery**: an `alg: none` self-signed token and an HS256 token signed with the app's own `SECRET_KEY` are both rejected — the app correctly relies on Firebase's real signature verification, not a naive decode (`tests/security/test_authentication.py`).
- **Cross-tenant data leaks (IDOR)**: exhaustively checked across every `/history` and `/users/me` operation with two simultaneously-authenticated identities — no leak in either direction, including bulk `DELETE /history` and `DELETE /users/me` cascades (`tests/security/test_authorization_idor.py`).
- **CORS**: explicit origin allow-list, not `*`; disallowed origins get no `Access-Control-Allow-Origin` header at all (`tests/security/test_configuration_headers.py`).
- **Error sanitization**: an unhandled exception in a route never leaks a stack trace or internal detail to the client — confirmed the sanitized generic body is what a *real* server returns (see the test-infra note below for why this needed a dedicated fixture to prove correctly) (`tests/functional/test_system_functional.py::test_global_exception_handler_hides_internals`).
- **Rate limiting**: `/scan/analyse` and `/scan/barcode` each independently enforce their documented 30/minute limit; confirmed under a full 84-second k6 run with 0 unexpected errors.

## Test-infrastructure findings

These aren't application bugs, but they're real discoveries made while
building this suite, and matter for anyone extending it later:

1. **Fixture design bug (fixed):** the original single-user auth-mocking pattern (`app.dependency_overrides[get_current_user_optional] = lambda: mock_auth_user`) silently breaks the moment a test needs two simultaneously-active identities — which every cross-tenant/IDOR test does. `app.dependency_overrides` is one global dict; whichever fixture's setup ran last wins for *every* client in the test, regardless of which client object made the request. Fixed by encoding identity in each client's own `Authorization` header, decoded fresh per-request (see `tests/conftest.py`, `_decode_test_identity`).
2. **Rate limiter shares global state across the whole pytest session (fixed):** `slowapi`'s in-memory store is keyed by client IP, and every `ASGITransport` test client presents the same IP — so tests can silently "spend" each other's quota depending on run order. Fixed with an autouse `limiter.reset()` fixture.
3. **Coverage under-reporting (fixed):** `coverage.py`'s default tracer doesn't follow code executed inside SQLAlchemy's async→sync `greenlet_spawn` bridge or FastAPI's thread-pooled sync dependency resolution. Reported coverage jumped from 84% to an accurate 92% (`app/routers/user.py` 51%→98%, `app/core/deps.py` 42%→95%) after adding `concurrency = greenlet,thread` to `.coveragerc`.
4. **`httpx.ASGITransport` doesn't reproduce production exception handling by default:** confirmed against a real `uvicorn` process *and* `ASGITransport` side-by-side — a real server correctly returns the app's sanitized 500 JSON body for an unhandled exception; the default test transport (`raise_app_exceptions=True`) instead re-raises the raw exception into the test process. A naive test would have looked like the handler was broken when it wasn't. Fixed with a dedicated `crash_test_client` fixture (`raise_app_exceptions=False`) used only where it's needed.
5. **The live server cannot boot at all without Firebase credentials outside pytest:** confirmed `sys.exit(1)` when `FIREBASE_CREDENTIALS_PATH` is missing/invalid and `"pytest" not in sys.modules`. This blocks k6/real-HTTP testing entirely unless something satisfies `firebase_admin.initialize_app()`. Worked around for CI with a throwaway, locally-generated (fake, no real secrets) service-account JSON — see `tests/reporting/ci_helpers/gen_fake_firebase_creds.py`. This cannot and does not produce a verifiable ID token, so authenticated endpoints are still out of scope for k6 — see the handover README's "Known testing gaps".
