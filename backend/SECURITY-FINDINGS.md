# Backend Test Findings — nutriscan-ai

All findings below were **confirmed by direct testing** against the real
application (not inferred from reading code), and each one has a
corresponding regression test in `tests/` so it can't silently regress or
silently get "fixed" without anyone noticing. The machine-readable version
of this table is `tests/reporting/output/findings.xlsx` (regenerate with
`python tests/reporting/generate_reports.py`).

## The headline finding

**The fuzzy ingredient matcher is case-sensitive in a way that breaks
real-world use, and it's a food-safety bug.** `IngredientEngine` lowercases
the ingredient a user types before matching, but compares it against
`ecodes.json`'s additive database in that file's *original* mixed case
(`"Sunset Yellow FCF"`, not `"sunset yellow fcf"`). `rapidfuzz`'s
`fuzz.WRatio` is case-sensitive — confirmed directly: `WRatio("sunset
yellow fcf", "sunset yellow fcf")` scores `100.0`, but `WRatio("sunset
yellow fcf", "Sunset Yellow FCF")` scores only `70.6`. That's below the
code's own 80-point confidence threshold.

Measured across **all 30** entries in the additive database (not just the
obvious ones):

- **23 of 30** score under 90 due to the case penalty alone — fragile, one
  small wording tweak to `ecodes.json` could tip any of these into failure
- **5 of 30 are confirmed broken outright** — either scoring below the
  80-point threshold, or losing to a different, wrong entry:

| Additive | Real status | What happens |
|---|---|---|
| Sunset Yellow FCF | danger | Scores 70.6, below threshold → silently falls through to **"safe"** |
| Allura Red AC | danger | Scores 69.2, below threshold → silently falls through to **"safe"** |
| Brilliant Blue FCF | caution | Scores 72.2, below threshold → silently falls through to **"safe"** |
| Plain Caramel | safe | Scores 84.6 vs its own entry, but 85.5 vs a *different* entry ("Sulphite ammonia caramel") → actively **misclassified as caution** |
| Guar Gum | safe | Scores 75.0, below threshold → identification is broken, only masked because the "safe" default happens to match its real status |

A user who scans a product and types (or a future OCR pipeline extracts)
an additive's name exactly as printed on the real label — the only case
any real user would ever actually see — can have a known-dangerous
synthetic dye silently pass as "safe". This is the single most significant
finding in this suite.

**Fix (one line):** lowercase the choices list before fuzzy matching, not
just the query:
```python
full_names_lower = [n.lower() for n in full_names]
match = process.extractOne(lower_name, full_names_lower, scorer=fuzz.WRatio)
ecode_match = next(e for e in self.ecodes if e["full_name"].lower() == match[0])
```

**Tests:** `tests/unit/test_ingredient_engine_matrix.py::test_ecode_matched_by_real_label_full_name`
and `::test_ecode_actually_identified_by_real_label_full_name` (strict xfail on the 5 confirmed entries — will XPASS-fail the moment this is fixed, as a reminder to remove the marker).

## All other findings

| Severity | Finding | Where | Regression test |
|---|---|---|---|
| Critical | `POST /history` doesn't exist (405) even though the mobile app's offline-sync flow expects it — matches the gap already flagged in `docs/AUDIT_REPORT.md` | `app/routers/history.py` | `tests/functional/test_history_functional.py::test_post_history_should_accept_offline_scan_sync` (strict xfail) |
| Medium | History ordering is not reliably newest-first: `scanned_at` uses `server_default=func.now()`, and SQLite's `CURRENT_TIMESTAMP` only has **second** granularity. Several scans within the same second tie, and with no secondary sort key the tie-break isn't what a user would expect. **Fix:** add `id DESC` as a secondary sort key | `app/routers/history.py` line ~48 | `tests/functional/test_history_functional.py::test_history_ordered_newest_first` (strict xfail) |
| Medium | `BarcodeRequest.barcode` has no format/character validation. Confirmed live: a barcode of `"../../../etc/passwd"` produces the literal outbound request `.../api/v2/product/../../../etc/passwd.json`. Low impact today (host is hardcoded), but exactly the shape that becomes exploitable if reused elsewhere | `app/schemas/scan.py`, `app/services/off_client.py` | `tests/security/test_input_validation_injection.py::test_barcode_value_reaches_outbound_url_unsanitized` |
| Low | A "safe"-status ingredient can still lose points in `calculate_hs_score` if its name contains "sugar"/"syrup"/"palm oil"/"fructose" — an independent keyword check runs regardless of the ingredient's own status. Confirmed: `["water","salt","sugar"]` scores 92, not 100, solely because of "sugar". Not necessarily wrong, but undocumented and inconsistent with the ingredient's own reported "No major concerns found." reason | `app/services/ingredient_engine.py`, `calculate_hs_score` | `tests/unit/test_ingredient_engine_matrix.py::test_safe_status_ingredient_still_penalized_if_name_contains_sugar_keyword` |
| Low | A medical condition outside the hardcoded set (Diabetes/Hypertension/High Cholesterol) is accepted by the schema (`conditions: List[str]`, no enum) but silently has zero effect on scoring — no error, no warning | `app/services/ingredient_engine.py`, `calculate_hs_score` | `tests/unit/test_ingredient_engine_matrix.py::test_unrecognized_condition_name_is_silently_ignored` |
| Low | No hardening headers (`X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, CSP) on any response | `app/main.py` | `tests/security/test_configuration_headers.py::test_no_hardening_security_headers_present` |
| Low | `/users/me` and `/history` have no rate limit at all (only `/scan/*` does). Low risk since both require a valid authenticated identity, but a compromised/leaked token currently has no throttle | `app/routers/user.py`, `app/routers/history.py` | `tests/security/test_rate_limiting.py::test_authenticated_endpoints_have_no_rate_limit_configured` |
| Informational | `/docs` and `/openapi.json` are exposed with FastAPI's defaults — hands out a full endpoint/parameter map for free. Worth a deliberate choice for production, not a leftover default | `app/main.py` (`FastAPI(...)` constructor) | `tests/security/test_configuration_headers.py::test_openapi_schema_is_reachable` |

## Things checked and confirmed **not** to be a problem

Worth recording explicitly — a passing test here is doing real work, not
just padding a count:

- **SQL injection**: SQLAlchemy's ORM parameterizes everything; injection-style strings in ingredient names, allergy lists, and display names are stored/returned as inert data.
- **JWT forgery**: an `alg: none` self-signed token and an HS256 token signed with a guessed secret are both rejected across every protected endpoint (77-case matrix: 11 token types × 7 endpoints) — the app correctly relies on Firebase's real signature verification, not a naive decode.
- **Cross-tenant data leaks (IDOR)**: exhaustively checked across every `/history` and `/users/me` operation with two simultaneously-authenticated identities — no leak in either direction, including bulk `DELETE /history` and `DELETE /users/me` cascades.
- **CORS**: explicit origin allow-list, not `*`; disallowed origins get no `Access-Control-Allow-Origin` header at all.
- **Error sanitization**: an unhandled exception in a route never leaks a stack trace or internal detail to the client — confirmed the sanitized generic body is what a *real* server returns (see the test-infra note below).
- **Rate limiting**: `/scan/analyse` and `/scan/barcode` each independently enforce their documented 30/minute limit; confirmed under a full 84-second k6 run with 0 unexpected errors.
- **HTTP method routing**: every unimplemented (route, method) combination across all 7 routes correctly returns 405, never a fallthrough to the wrong handler or a raw 500.
- **The E-code and NOVA-marker databases themselves**: every one of the 30 additives and 20 NOVA markers is individually confirmed present and correctly wired when matched by its short code / exact keyword (the case-sensitivity bug above is specifically about the *fuzzy* full-name path, not the data or the direct-match path).

## Test-infrastructure findings

These aren't application bugs, but they're real discoveries made while
building this suite, and matter for anyone extending it later:

1. **Fixture design bug (fixed):** the original single-user auth-mocking pattern (`app.dependency_overrides[get_current_user_optional] = lambda: mock_auth_user`) silently breaks the moment a test needs two simultaneously-active identities — which every cross-tenant/IDOR test does. `app.dependency_overrides` is one global dict; whichever fixture's setup ran last wins for *every* client in the test, regardless of which client object made the request. Fixed by encoding identity in each client's own `Authorization` header, decoded fresh per-request (see `tests/conftest.py`, `_decode_test_identity`).
2. **Rate limiter shares global state across the whole pytest session (fixed):** `slowapi`'s in-memory store is keyed by client IP, and every `ASGITransport` test client presents the same IP — so tests can silently "spend" each other's quota depending on run order. Fixed with an autouse `limiter.reset()` fixture.
3. **Coverage under-reporting (fixed):** `coverage.py`'s default tracer doesn't follow code executed inside SQLAlchemy's async→sync `greenlet_spawn` bridge or FastAPI's thread-pooled sync dependency resolution. Reported coverage jumped from 84% to an accurate 94% (`app/routers/user.py` 51%→98%, `app/core/deps.py` 42%→95%) after adding `concurrency = greenlet,thread` to `.coveragerc`.
4. **`httpx.ASGITransport` doesn't reproduce production exception handling by default:** confirmed against a real `uvicorn` process *and* `ASGITransport` side-by-side — a real server correctly returns the app's sanitized 500 JSON body for an unhandled exception; the default test transport (`raise_app_exceptions=True`) instead re-raises the raw exception into the test process. Fixed with a dedicated `crash_test_client` fixture (`raise_app_exceptions=False`) used only where it's needed.
5. **The live server cannot boot at all without Firebase credentials outside pytest:** confirmed `sys.exit(1)` when `FIREBASE_CREDENTIALS_PATH` is missing/invalid and `"pytest" not in sys.modules`. Worked around for CI/k6 with a throwaway, locally-generated (fake, no real secrets) service-account JSON — see `tests/reporting/ci_helpers/gen_fake_firebase_creds.py`.
6. **A raw unicode/emoji string is not a testable "malformed token" case:** `httpx` refuses client-side to encode non-ASCII bytes into an HTTP header at all (`UnicodeEncodeError`), before a request is ever sent. That's not a gap in the auth matrix — it's not a scenario any real HTTP client could produce over the wire in the first place, so it was correctly excluded rather than worked around.

## Test suite scale

409 test cases total (398 passing, 11 strict-`xfail` documenting the
confirmed bugs above), up from an initial pass of 116. The increase came
almost entirely from legitimate data-driven matrices — every one of the 30
`ecodes.json` entries, every one of the 20 NOVA markers, every protected
endpoint crossed with every invalid-token type, every registered route
crossed with every HTTP method — not from duplicating scenarios. The
E-code matrix in particular is what surfaced the headline finding above;
a smaller, non-exhaustive sample would very plausibly have missed it.
