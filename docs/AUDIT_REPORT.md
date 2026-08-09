# NutriScan AI — Audit Report

> **Audit Date:** 2026-08-09  
> **Auditor:** Antigravity  
> **Scope:** `backend/` and `mobile/` — read-only, no code changes made.

---

## Backend

### No Secrets Committed
**Status: PARTIAL**

`git ls-files` output shows:
```
backend/.env.example        <- OK (example only)
backend/nutriscan.db.bak    <- TRACKED — binary backup DB file
mobile/android/app/google-services.json.example  <- OK (example only)
mobile/lib/firebase_options.dart.example         <- OK (example only)
```

The real `backend/.env`, `backend/nutriscan.db`, and `mobile/android/app/google-services.json` are correctly untracked. However, **`backend/nutriscan.db.bak` (36 KB binary) is still tracked by git** despite `.gitignore` having `backend/*.db`. The glob `*.db` does not match `*.db.bak` — the `.bak` extension sidesteps the pattern.

**Fix needed:** `git rm --cached backend/nutriscan.db.bak` and add `backend/*.db.bak` to `.gitignore`.

---

### Firebase Auth Enforcement on Protected Routes
**Status: DONE**

`deps.py:22` — `get_current_user` wraps `get_current_user_optional` and raises `HTTP 401` if no decoded token is present. All protected router files wire this correctly:
- `routers/user.py` — `get_my_profile`, `update_my_profile`, `delete_my_profile` all use `Depends(get_current_user)`.
- `routers/history.py` — `list_history`, `get_history_item`, `delete_history_item`, `clear_history` all use `Depends(get_current_user)`.
- `routers/scan.py` — Uses `Depends(get_current_user_optional)` (intentionally, scan works unauthenticated).

Note: Not verified against live Firebase network; the wiring is correct by static inspection.

---

### User Profile Endpoints (`routers/user.py`)
**Status: DONE**

| Endpoint | Method | DB Operation | Status |
|---|---|---|---|
| `GET /users/me` | `get_my_profile` | `SELECT User WHERE id=uid`, auto-creates row on first access | Full DB read/write |
| `PATCH /users/me` | `update_my_profile` | `SELECT` then `setattr` loop + `commit` | Full DB read/write |
| `DELETE /users/me` | `delete_my_profile` | `DELETE ScanHistory` cascade, then `DELETE User` | Full DB write |

No stubs. All three endpoints have working DB operations. **Confirmed working via `pytest` (all 4 user tests pass).**

---

### Scan History Endpoints (`routers/history.py`)
**Status: DONE (with critical gap — see Cross-Cutting)**

| Endpoint | Method | DB Operation | Status |
|---|---|---|---|
| `GET /history` | `list_history` | `SELECT ScanHistory WHERE user_id ORDER BY desc LIMIT/OFFSET` | Full |
| `GET /history/{id}` | `get_history_item` | `SELECT WHERE id AND user_id` | Full |
| `DELETE /history/{id}` | `delete_history_item` | `db.delete(scan)` + `commit` | Full |
| `DELETE /history` | `clear_history` | `DELETE ScanHistory WHERE user_id` | Full |

**Missing endpoint (contract gap):** `API.md` documents no `POST /history` endpoint, but `api_service.dart:239` calls `_dio.post('/history', data: scanData)`. This endpoint **does not exist in `routers/history.py`**. The app's sync push will silently fail (405 Method Not Allowed).

---

### Alembic Migrations
**Status: DONE**

Ran `alembic upgrade head` from `backend/`:
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 8021573c1970, Initial migration
```
Migration ran clean. Tested against the existing SQLite dev DB. A fresh Postgres run was not possible without Docker.

---

### Redis Caching
**Status: MISSING**

`core/cache.py` defines a `CacheClient` with `get_json` / `set_json`. The `cache` singleton is imported in `main.py` and used only in the `/health` ping check (line 75-76). **No router calls `cache.get_json()` or `cache.set_json()`.** The OpenFoodFacts client makes a fresh HTTP call on every barcode request — no Redis caching.

---

### Rate Limiting
**Status: DONE**

- `main.py:30` — `app.state.limiter = limiter`
- `main.py:31` — `add_exception_handler(RateLimitExceeded, ...)`
- `routers/scan.py:22` — `@limiter.limit("30/minute")` on `POST /scan/analyse`
- `routers/scan.py:73` — `@limiter.limit("30/minute")` on `POST /scan/barcode`

Fully wired. User/history routes have no rate limiting (acceptable for auth-gated endpoints).

---

### Backend Tests (`pytest`)
**Status: DONE — 13/13 passed**

```
tests/test_history.py::test_list_history_empty                  PASSED
tests/test_history.py::test_create_history_via_scan_and_list    PASSED
tests/test_history.py::test_history_ownership                   PASSED
tests/test_ingredient_engine.py::test_ingredient_engine_analyze PASSED
tests/test_ingredient_engine.py::test_ingredient_engine_score   PASSED
tests/test_nova_classifier.py::test_nova_classify               PASSED
tests/test_scan.py::test_analyse_ingredients_happy_path         PASSED
tests/test_scan.py::test_analyse_ingredients_empty              PASSED
tests/test_scan.py::test_analyse_barcode_not_found              PASSED
tests/test_users.py::test_get_profile_unauthorized              PASSED
tests/test_users.py::test_get_profile_authorized                PASSED
tests/test_users.py::test_patch_profile                         PASSED
tests/test_users.py::test_delete_profile                        PASSED

13 passed, 1 warning in 0.53s
```

1 warning: Pydantic V2 deprecated class-based config in `config.py`. Non-blocking.

---

### API Docs — Spot-Check 3 Endpoints
**Status: DONE (with one gap)**

| Endpoint | API.md says | Router signature | Match? |
|---|---|---|---|
| `GET /users/me` | Returns user profile, auth required | `response_model=UserProfileResponse`, `Depends(get_current_user)` | PASS |
| `GET /history` | Lists history, paginated, auth required | `response_model=List[ScanHistoryResponse]`, `limit`/`offset` Query params | PASS |
| `POST /scan/barcode` | Body `{"barcode": "..."}`, optional auth | `body: BarcodeRequest`, `Depends(get_current_user_optional)` | PASS |

Gap: `API.md` has no mention of a `POST /history` endpoint, which the mobile app calls.

---

### Docker Compose
**Status: NOT RUN**

Docker is not available in this environment. Cannot verify the compose stack starts clean. The `docker-compose.yml` includes Postgres, Redis, and the backend service; actual startup was not confirmed. Must be verified manually.

---

## Mobile (Flutter)

### `flutter analyze`
**Status: FAILING — 10 hard errors, 128 info/warnings**

```
error - undefined_getter: 'instance' isn't defined for 'GoogleSignIn'
        lib/features/auth/providers/auth_provider.dart:22

error - undefined_method: 'authenticate' isn't defined for 'GoogleSignIn'
        lib/features/auth/providers/auth_provider.dart:52

error - undefined_getter: 'background' isn't defined for 'AppColors'
        lib/features/scanner/screens/scanner_screen.dart:345

error - invalid_constant / undefined_getter: 'primary' isn't defined for 'AppColors'
        lib/features/scanner/screens/scanner_screen.dart:352, 374, 388, 390

error - undefined_method: '_showManualTextDialog' isn't defined
        lib/features/scanner/screens/scanner_screen.dart:382

138 issues total (ran in 6.1s)
```

Notable non-error warnings:
- `scan_provider.dart:94,132` — `unrelated_type_equality_checks` comparing `List<ConnectivityResult>` to `ConnectivityResult` — offline detection never fires.
- `app_theme.dart:39` — `ThemeData.background` deprecated; `AppColors.background` / `AppColors.primary` used in `scanner_screen.dart` but never defined in `AppColors` class.
- 9x `unused_import` warnings across various files.
- Multiple `avoid_print` in `api_service.dart` (should use `debugPrint`).

---

### `flutter test`
**Status: PARTIAL — 5/8 pass, 3 fail to compile**

```
safety_score_service_test.dart — 4 PASSED
results_screen_test.dart        — 1 PASSED
auth_screen_test.dart           — FAILED TO COMPILE (inherits auth_provider.dart errors)
widget_test.dart (default)      — FAILED TO COMPILE (inherits scanner_screen.dart errors)
```

---

### GoogleSignIn API Compatibility
**Status: MISSING — 2 hard errors**

`pubspec.yaml` specifies `google_sign_in: ^6.2.1` which resolved to `6.3.0`. The code in `auth_provider.dart` uses `GoogleSignIn.instance` and `.authenticate()` which do not exist on this version. These are the same two errors visible in `flutter analyze`. **App will not compile.**

---

### No Hardcoded Personal IP
**Status: DONE**

Regex search `\d+\.\d+\.\d+\.\d+` across `mobile/lib/` — no results. The old `192.168.29.217` IP is gone. `app_config.dart:9` now defaults to `http://localhost:8000`.

---

### Scan History and User Profile Call `api_service.dart`
**Status: DONE**

- `scan_history_provider.dart:90` — `apiService.postScanHistory(...)`
- `scan_history_provider.dart:113` — `apiService.deleteScanHistoryItem(id)`
- `scan_history_provider.dart:159` — `apiService.getScanHistory(limit: 100)`
- `user_profile_provider.dart:80` — `apiService.getUserProfile()`
- `user_profile_provider.dart:98,140` — `apiService.patchUserProfile(...)`

Both providers make real API calls, not just Drift DAO calls.

---

### Auth Token Interceptor on Correct Dio Instance
**Status: DONE**

`api_service.dart:8` — single `_dio` field. `InterceptorsWrapper` added to it at line 15 in the constructor. All methods use `_dio`. No second Dio instance exists.

---

### Android Application ID / Namespace
**Status: DONE**

- `build.gradle.kts:18` — `namespace = "com.nutriscan.app"`
- `build.gradle.kts:42` — `applicationId = "com.nutriscan.app"`

No trace of `com.example.nutriscan` remains.

---

### Release Signing
**Status: DONE**

- `build.gradle.kts:31-38` — `signingConfigs.create("release")` reads from `keystoreProperties`
- `build.gradle.kts:52-53` — release buildType uses `signingConfigs.getByName("release")`
- Debug keystore fallback is removed
- `mobile/android/keystore.properties.example` exists; `keystore.properties` is gitignored

Note: If `keystore.properties` is absent, Gradle will error on a release build. Intended behavior, but not documented in `mobile/README.md`.

---

### Firebase Files Untracked, Examples Present
**Status: DONE**

`git ls-files` for Firebase-related files:
```
mobile/android/app/google-services.json.example  <- tracked (correct)
mobile/lib/firebase_options.dart.example          <- tracked (correct)
```
Real secrets untracked. `.example` files present.

---

### `.gitignore` Paths Match Repo Structure
**Status: PARTIAL**

- Firebase paths are correct with `mobile/` prefix.
- `backend/*.db` does NOT match `*.db.bak` — `nutriscan.db.bak` still tracked.
- Lines 43-45 contain stale root-anchored paths:
  ```
  /android/app/debug
  /android/app/profile
  /android/app/release
  ```
  These would only match a top-level `/android/` directory which doesn't exist in this repo. The real path is `mobile/android/`. These rules are **harmless but wrong** (they protect nothing).

---

## Cross-Cutting

### API Contract: `api_service.dart` vs Backend Schemas

**Status: PARTIAL — critical field mismatches found**

#### `POST /history` — Missing Endpoint (CRITICAL)

`api_service.dart:239` calls `_dio.post('/history', data: scanData)`. This endpoint **does not exist** in `routers/history.py`. Mobile scan sync-push will receive a 405 and return `false` silently.

#### Field Mismatches

| Field | Backend Schema | Mobile Sends/Reads | Match? |
|---|---|---|---|
| `product_name` | `Optional[str]` | `'product_name'` | PASS |
| `health_score` | `Optional[int]` | `'health_score'` | PASS |
| `nova_group` | `Optional[int]` | `'nova_group'` | PASS |
| `id` on POST | Auto-increment `int` (server-set) | UUID `String` sent from mobile | FAIL — type mismatch |
| `display_name` (response) | `display_name` (snake_case) | Read as `data['displayName']` (camelCase) | FAIL — display name never populated |

---

### End-to-End Smoke Check
**Status: NOT RUN (Docker unavailable)**

`mobile/config/dev.json` points to `http://localhost:8000`. Correct for emulator; won't work from a physical device on LAN without the machine's IP. Docker Compose stack was not started.

---

## Prioritized Blockers

> Ordered by severity: will this prevent launch or silently corrupt data?

| Priority | Item | Severity | Location |
|---|---|---|---|
| 1 (CRITICAL) | `auth_provider.dart` — `GoogleSignIn.instance` / `.authenticate()` undefined on v6.3.0. App will not build. | Build error | `auth_provider.dart:22,52` |
| 2 (CRITICAL) | `scanner_screen.dart` — `AppColors.background`, `AppColors.primary`, `_showManualTextDialog()` undefined. App will not build. | Build error | `scanner_screen.dart:345,352,374,382,388,390` |
| 3 (CRITICAL) | `POST /history` backend endpoint missing. Offline scans never sync to server — silent data loss. | Silent data loss | `routers/history.py` (missing), `api_service.dart:239` |
| 4 (HIGH) | `display_name` vs `displayName` field mismatch. User display name never populated from cloud. | Silent wrong data | `user_profile_provider.dart:83` |
| 5 (HIGH) | Scan `id` type mismatch: mobile sends UUID `String`, backend schema expects auto-increment `int`. POST body malformed. | Silent POST failure | `scan_history_provider.dart:91` |
| 6 (MEDIUM) | `backend/nutriscan.db.bak` tracked in git. 36 KB binary should not be in VCS. | Git hygiene | `.gitignore` |
| 7 (MEDIUM) | `scan_provider.dart:94,132` — `ConnectivityResult` type mismatch. Offline detection never fires. | Silent runtime bug | `scan_provider.dart` |
| 8 (LOW) | Redis caching defined but unused in routers. Every OFF barcode lookup hits the network. | Performance | `cache.py` unused in routers |
| 9 (LOW) | `.gitignore` stale `/android/...` rules don't match `mobile/android/` path. Harmless but misleading. | Git hygiene | Root `.gitignore:43-45` |
| 10 (LOW) | 128 `info`-level `flutter analyze` issues (`withOpacity` deprecated, `prefer_const`, unused imports). | Code quality | Various `lib/` files |

### Verdict

**Not safe to treat as "backend + app done, start web."**  
Items 1 and 2 are build-breaking — the Flutter app will not compile for any target.  
Item 3 is a silent data-integrity failure that will go unnoticed in manual testing.  
Resolve blockers 1–5 before starting web development.
