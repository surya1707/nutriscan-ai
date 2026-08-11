# nutriscan-ai — Backend Test Suite Handover

This is a complete backend testing setup for `github.com/surya1707/nutriscan-ai`
— functional tests, security/IDOR tests, a k6 load test, CI, and reporting —
built by cloning your real repo, running its real code, and confirming
every claim below by direct testing rather than by reading the code and
assuming. Where that testing turned up real bugs, they're documented with
regression tests, not silently worked around.

**Read this first:** this repo has ~11 backend endpoints across 3 routers.
The methodology you gave me (`final_year.md`) was written against a much
larger reference project and asks for 400+ structured test cases. Forcing
that number onto an app this size would mean padding with near-duplicate,
low-value tests — which the methodology itself explicitly warns against
("test what is actually there rather than fabricating tests"). I scaled to
the real surface area instead: **116 real test cases** (87 test functions,
several parametrized) across functional, security, authentication,
authorization/IDOR, injection, rate-limiting, and configuration categories,
plus a load test and CI pipeline. Every test either passes against the real
app or is a strict `xfail` documenting a confirmed, real bug. See
`backend/SECURITY-FINDINGS.md` for the full list of what was found.

---

## 1. What's in this zip

```
backend/
  tests/
    conftest.py                          # extended — see "fixture redesign" below
    test_history.py, test_ingredient_engine.py,      # UNCHANGED — your original
    test_nova_classifier.py, test_scan.py,           # 13 tests, still pass
    test_users.py                                    # exactly as before
    functional/                          # 45 new tests: scan, users, history, system
    security/                            # 58 new tests: auth, IDOR, injection,
                                          #   rate limiting, CORS/headers
    reporting/
      generate_reports.py                # builds the xlsx catalog + findings workbook
      ci_helpers/gen_fake_firebase_creds.py
      output/                            # generated, not committed (see .gitignore note)
  load/
    k6-load-test.js                      # k6 load/smoke test, validated end-to-end
  requirements-test.txt                  # pytest-cov, openpyxl, bandit, pip-audit, etc.
  .coveragerc                            # fixes a real coverage under-reporting bug
  SECURITY-FINDINGS.md                   # human-readable findings, mirrors findings.xlsx
.github/
  workflows/
    backend-tests.yml                    # SAST + tests + k6, on push/PR/dispatch
```

## 2. How to merge this into your repo

Everything mirrors your repo's real folder layout, so it's a straight copy:

```bash
git clone https://github.com/surya1707/nutriscan-ai.git
cd nutriscan-ai

# copy in this handover's contents (adjust the source path to wherever you unzipped it)
cp -r /path/to/handover/backend/tests/*        backend/tests/
cp -r /path/to/handover/backend/load           backend/
cp    /path/to/handover/backend/requirements-test.txt  backend/
cp    /path/to/handover/backend/.coveragerc            backend/
cp    /path/to/handover/backend/SECURITY-FINDINGS.md   backend/
cp -r /path/to/handover/.github                .

git add -A
git commit -m "Add functional/security backend test suite, load test, and CI"
```

`tests/conftest.py` is **replaced**, not merged — see section 4 for exactly
what changed and why; it's a drop-in replacement, your original 13 tests
run against it unmodified and unchanged.

## 3. Running it locally

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt -r requirements-test.txt

export DATABASE_URL="sqlite+aiosqlite:///:memory:"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="local-dev-secret"
export ENVIRONMENT="development"
export ALLOWED_ORIGINS="http://localhost:5173,https://nutriscan.app"

# run everything
python -m pytest tests/ -v

# with coverage (uses the .coveragerc fix — see finding #3 in SECURITY-FINDINGS.md)
python -m pytest tests/ --cov=app --cov-report=term-missing

# generate the xlsx test-case catalog + findings workbook
python -m pytest tests/ --json-report --json-report-file=/tmp/pytest-report.json
python tests/reporting/generate_reports.py
# -> tests/reporting/output/test-case-catalog.xlsx
# -> tests/reporting/output/findings.xlsx
```

Expected result: **114 passed, 2 xfailed**. The 2 xfails are real, confirmed
bugs (not test problems) — see `SECURITY-FINDINGS.md`. If either one ever
shows as `XPASS` instead, it means someone fixed the underlying bug and the
`xfail` marker should be deleted from that test.

Confirmed to be order-independent and stable — ran the full suite
back-to-back multiple times with identical results.

### Running the k6 load test

```bash
# terminal 1: boot a real live server (needs SOME firebase creds file to start at all --
# see SECURITY-FINDINGS.md item 5. For local use, your real Firebase creds work fine.)
cd backend
export DATABASE_URL="sqlite+aiosqlite:///./local_load_test.db"
export REDIS_URL="redis://localhost:6379/0"
export SECRET_KEY="local-dev-secret"
export ENVIRONMENT="development"
export ALLOWED_ORIGINS="http://localhost:5173"
export FIREBASE_CREDENTIALS_PATH="/path/to/your/real-or-throwaway-creds.json"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# terminal 2: install k6 (https://k6.io/docs/get-started/installation/), then:
BASE_URL=http://127.0.0.1:8000 k6 run backend/load/k6-load-test.js
```

This was run end-to-end in the sandbox that built this handover: a full
84-second run against a real live instance completed with **100% of checks
passing**, 0 unexpected 5xx errors, and the 30/minute rate limit on
`/scan/*` correctly kicking in under sustained load.

## 4. What changed in `conftest.py`, and why

Your original `conftest.py`'s auth-mocking pattern
(`app.dependency_overrides[get_current_user_optional] = lambda: mock_auth_user`)
works perfectly for one authenticated client per test — which is all your
original 13 tests ever needed. It breaks silently the moment a test needs
**two** simultaneously-active identities, which every cross-tenant/IDOR
test requires by definition (`app.dependency_overrides` is one global dict;
whichever fixture's setup runs last wins for every client in the test).
Confirmed empirically before fixing it: every IDOR test using
`auth_client` + `auth_client_2` together returned the *second* identity's
data down *both* clients.

The fix: identity is now encoded in each client's own `Authorization`
header and decoded fresh per real request, so two clients hitting the same
app resolve independently and correctly. `auth_client` and `async_client`
keep their original names and exactly their original observable behavior —
your 13 original tests pass against the new `conftest.py` unmodified.

New fixtures added (all documented in the file itself):
`auth_client_2` (second identity), `make_auth_client` (factory for
malformed/edge-case identity claims), `raw_client` (real, unmocked auth —
for testing that bad tokens are genuinely rejected), `crash_test_client`
(the one place a plain `async_client` gives a misleading result — see
finding #4), and an autouse rate-limiter reset (finding #2).

## 5. Known testing gaps (stated plainly, not hidden)

- **A genuinely valid Firebase ID token can never be tested in this CI.**
  `raw_client`-based tests (in `tests/security/test_authentication.py`)
  exhaustively prove that missing, malformed, forged, and garbage tokens
  are all rejected — but there's no live Firebase project available here to
  mint a real, valid token, so the "valid token is accepted" direction is
  untested by this suite. If you want that closed, the standard options
  are the [Firebase Auth
  emulator](https://firebase.google.com/docs/emulator-suite) in CI, or a
  disposable test-only Firebase project with a service account CI can use
  to mint real tokens.
- **k6 only load-tests the endpoints that don't require a verified token**
  (`/health`, `/`, `/scan/analyse`, `/scan/barcode`) for the same root
  reason — see `backend/load/k6-load-test.js`'s header comment and finding
  #5. `/users/me` and `/history` are functionally covered by pytest but not
  load-tested.
- **`off_client.py`'s network-error branches** (timeout, connection error)
  are only partially covered — `app/services/off_client.py` sits at 65%
  coverage, the lowest in the codebase. Worth a follow-up if you want to be
  thorough there.

## 6. CI pipeline (`.github/workflows/backend-tests.yml`)

Three jobs, triggered on push/PR touching `backend/**`, or manually:

- **`sast`** — bandit (fails the build only on a HIGH-severity,
  HIGH-confidence finding; currently clean) + pip-audit (report-only;
  currently clean, no known CVEs in `requirements.txt`).
- **`backend-tests`** — the full pytest suite with a real `redis` service
  container, coverage, and the xlsx report generator. This is the merge
  gate: any non-`xfail` failure fails the build. Uploads the coverage HTML,
  JUnit XML, and both xlsx workbooks as artifacts.
- **`load-test`** — boots a real live server (throwaway CI-only Firebase
  credentials, see finding #5) and runs the full k6 script.
  `continue-on-error: true` — informational, doesn't block merges, since
  shared GitHub-hosted runners aren't a reliable environment for hard
  latency thresholds.

## 7. If you only have a few minutes to look at one thing

Open `backend/SECURITY-FINDINGS.md`. It's the same content as
`findings.xlsx` in prose form, and every row links to the exact test that
proves it.
