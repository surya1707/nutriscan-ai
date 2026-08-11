# NutriScan AI — Web App Selenium Test Suite

A complete Selenium + pytest E2E framework for the **web app only**
(`web/`), designed to run entirely inside **GitHub Actions** — no local
browser, no local Python environment, no local anything required. You
trigger it from the Actions tab (or a push), and it builds the app,
serves it, tests it, and uploads reports, all inside the runner.

---

## 1. Where these files go

Unzip this archive **into the root of your `nutriscan-ai` repo**, so you end up with:

```
nutriscan-ai/
├── .github/
│   └── workflows/
│       └── selenium-tests.yml      ← new
├── selenium-tests/                 ← new
│   ├── config.py
│   ├── conftest.py
│   ├── pytest.ini
│   ├── requirements.txt
│   ├── .gitignore
│   ├── pages/
│   ├── tests/
│   └── scripts/
├── web/                            ← already exists, untouched
├── backend/                        ← already exists, untouched
├── mobile/                         ← already exists, untouched
└── ...
```

Nothing in `web/`, `backend/`, or `mobile/` is modified. Commit and push:

```bash
git add .github/workflows/selenium-tests.yml selenium-tests/
git commit -m "Add Selenium web test suite"
git push
```

That's it — pushing to `main` with changes under `web/` or
`selenium-tests/` will trigger the workflow automatically. You can also
run it any time from **Actions → Web App Selenium Tests → Run workflow**.

---

## 2. What this tests, and what it deliberately does not

This suite covers **`web/` only** — matching the scope you asked for. It
does **not** start the FastAPI backend and does **not** touch `mobile/`.

### Why no backend?

Two real constraints, not laziness:

1. Your backend (`backend/app/core/firebase.py`) calls `sys.exit(1)` at
   import time if it can't find a Firebase Admin service-account JSON
   and isn't running under pytest. Spinning it up in this workflow would
   mean putting a Firebase Admin private key into GitHub Secrets and
   accepting the blast radius that comes with that, for a workflow whose
   job is to test the *frontend*.
2. It mirrors how your own repo already deploys — `deploy-web.yml`
   ships a static SPA to GitHub Pages with no backend anywhere near it.
   Testing "the web app as GitHub Pages actually serves it" means
   testing it **without** a backend sitting next to it.

So: every test that would need a live API (submitting a barcode scan,
loading real scan history) instead asserts that the **failure is
handled gracefully** — a visible error message, a loading spinner that
resolves instead of hanging forever, no crash. That's genuinely useful
coverage: it's exactly what a real user sees on a flaky connection or
during a backend outage. See `tests/test_scan_network_handling.py`.

### Why "guest mode" is the backbone of every other test

Your app's three login paths aren't equally testable in headless CI:

| Path | Automatable in CI? | Why |
|---|---|---|
| **Guest mode** | ✅ Yes, fully | Pure client-side — sets a `localStorage` flag, no network call (`authStore.ts: continueAsGuest`) |
| Google sign-in | ❌ No | Needs a real Google account + an interactive OAuth popup |
| Email magic-link | ⚠️ Only up to "link sent" | Completing it needs access to a real inbox |

So every test that needs to be "logged in" — navigation, history,
profile, scan validation, session management — logs in as a **guest**.
Google and email are tested only up to the boundary of what a headless
browser can safely observe (button exists, is clickable, client-side
validation fires, no silent crash) — see `tests/test_auth_login_page.py`.

### A real bug-shaped thing this suite is built around

`AppShell.tsx` renders **three navigation instances in the DOM
simultaneously** — a desktop sidebar, a mobile bottom bar, and a tablet
drawer — and switches which one is *visible* purely with CSS media
queries. A naive `find_element(By.LINK_TEXT, "History")` can silently
grab a hidden one and throw `ElementNotInteractableException`. Every
page object in `pages/` filters to elements that are actually
`is_displayed()` before clicking — see `pages/base_page.py` docstring
and `find_visible()` / `find_all_visible()`. `tests/test_navigation.py`
also has a dedicated regression check
(`test_exactly_one_visible_nav_instance_per_link_*`) that would catch it
if this ever broke.

---

## 3. Test inventory

**400 individual test cases** across these categories. Every single one
was grown for a real reason — more input-boundary values (unicode,
emoji, XSS/SQLi-shaped strings, extreme lengths), a full route-to-route
navigation matrix, exact-pixel breakpoint boundaries (767/768/769,
1023/1024/1025), keyboard-only operability, and heading/landmark
structure per page — not padded with `assert True` or duplicate-with-a-
different-name tests. Verify that any time you like:

```bash
grep -rn "or True\|assert True" selenium-tests/tests/    # → no matches
python -m pytest --collect-only -q selenium-tests/       # → 400 tests collected
```

| File | Category | What it covers |
|---|---|---|
| `test_auth_login_page.py` | Authentication | Login page rendering, guest flow, Google/email boundary checks, 20 malformed + 8 well-formed email variants, repeated-submission and toggle-state edge cases |
| `test_authorization_routes.py` | Authorization | Every protected route bounces unauth'd visitors to `/login`; guests pass through; strict vs. loose guest-flag value handling; cross-route consistency matrix |
| `test_navigation.py` | Navigation | Nav-bar links, full route-to-route matrix, multi-step back/forward chains, avatar menu, logout, tablet drawer, nav from every page, the triple-nav regression guard |
| `test_scan_validation.py` | Forms / Input Validation | Client-side validation on barcode + ingredients forms (20+ barcode variants, 15+ delimiter/ingredient variants, XSS/SQLi-shaped payloads, boundary lengths) |
| `test_scan_network_handling.py` | Error Handling | Graceful degradation when the (deliberately absent) backend is unreachable, retry behaviour, button re-enable timing |
| `test_history_page.py`, `test_profile_page.py`, `test_results_page.py` | Page-level (CRUD-adjacent) | Each protected page loads, survives reload/rapid reload, handles missing router state, display-name field boundary inputs |
| `test_ui_validation.py` | UI Validation | Heading structure, page titles, meta tags (viewport/charset/favicon), duplicate DOM ids, console errors, load-time budget, no leaked dev artifacts, form element types — across every page |
| `test_session_management.py` | Session Management | Guest session persists across reload/multi-page navigation, logout clears it, unrelated localStorage keys don't interfere, no stale-state login bypass |
| `test_accessibility.py` | Accessibility | `aria-label` on icon-only buttons, labeled form fields, native `<button>` elements, decorative SVG handling, heading-level skip detection, landmark regions, color-independent error indication |
| `test_keyboard_navigation.py` | Accessibility (keyboard) | Tab-order reachability, Enter/Space activation, visible focus indicators, Escape handling |
| `test_responsive.py` | Responsive | The app's own three real breakpoints, nav reachability at each, no horizontal overflow across every page × viewport |
| `test_breakpoint_boundaries.py` | Responsive (boundaries) | Exact pixel values the CSS switches at (767/768/769, 1023/1024/1025) — the off-by-one values most likely to actually break |
| `test_routing_deep_links.py` | Navigation / Routing | Direct deep-link loads (the GitHub Pages `404.html` SPA-redirect trick), reload-on-nested-route, query strings, hash fragments, encoded/duplicated path segments, hostile `results/:id` values |

---

## 4. How the CI workflow works

`.github/workflows/selenium-tests.yml`:

1. **Builds** `web/` with `npm install && npm run build` (only for the
   default `local-preview` target).
2. **Serves** the build with `vite preview` — this automatically
   respects `base: '/nutriscan-ai/'` from `vite.config.ts` *and*
   provides SPA history-fallback, so deep links like `/nutriscan-ai/scan`
   work the same way they do on GitHub Pages, without extra scripting.
3. **Health-checks** the target with a curl retry loop (30 attempts,
   2s apart) before touching Selenium — first-boot GitHub Pages deploys
   and cold `vite preview` starts aren't always instant.
4. **Installs Chrome** via `browser-actions/setup-chrome@v1` (not manual
   apt/GPG) and uses Selenium 4's built-in Selenium Manager — no
   `chromedriver` download step needed.
5. **Runs pytest** in parallel (`pytest-xdist`, default 4 workers) with
   automatic retries (`pytest-rerunfailures`, 2 reruns).
6. **Generates reports** as its own step, always, even if tests failed
   or were cancelled (`if: always()`), merging every xdist worker's
   result file.
7. **Uploads every report and screenshot as an artifact** — before the
   pass/fail gate is evaluated, so a bad run is still fully debuggable.
8. **Enforces the pass-rate gate last**, as a dedicated step reading
   the generated `execution-results.json` — not baked into pytest's own
   exit code. Default threshold: 95%, in one place
   (`config.PASS_RATE_THRESHOLD`), used consistently for both the
   displayed number and the enforcement check.

### Triggering it

- **Automatically**: push to `main` touching `web/` or `selenium-tests/`.
- **Manually**: Actions tab → "Web App Selenium Tests" → "Run workflow".
  You can override:
  - **target**: `local-preview` (default, self-contained) or `deployed`
    (tests the live GitHub Pages URL instead)
  - **base_url**: only used when `target=deployed`
  - **headless**: leave `true` unless you're debugging via the Actions
    log
  - **parallelism**: xdist worker count (default `4`)

### Optional secrets

None are required for the suite to pass. If you want the login-page
tests to reflect a fully-configured Firebase project (rather than an
empty config), set these repo secrets — the same ones `deploy-web.yml`
already uses:

```
VITE_API_URL
VITE_FIREBASE_API_KEY
VITE_FIREBASE_AUTH_DOMAIN
VITE_FIREBASE_PROJECT_ID
VITE_FIREBASE_STORAGE_BUCKET
VITE_FIREBASE_MESSAGING_SENDER_ID
VITE_FIREBASE_APP_ID
```

Guest-mode tests (the majority of the suite) work identically either way.

---

## 5. Reading the results

After a run, open the workflow run in the Actions tab:

- **Job Summary** tab shows a pass/fail/skip count table straight away
  (from `reports/summary.md`).
- **Artifacts** (bottom of the run page):
  - `selenium-reports` — `Automation_Test_Report.xlsx` (Executed Tests /
    Passed / Failed / Skipped / Execution Metrics / Defect Summary
    sheets), `execution-report.html`, `dashboard.html`,
    `execution-results.json`, `summary.md`, plus `logs/`.
  - `selenium-screenshots` — one PNG per failed test, filenames
    sanitized so GitHub's artifact upload never silently drops one.

If the job is red, it's always the **last** step ("Enforce pass-rate
gate") that failed — scroll up to "Run Selenium tests" for the actual
pytest failures, or just open the XLSX/HTML report.

---

## 6. Running locally (optional — not required for this task)

Everything above is designed to need zero local setup. If you ever want
to run a subset locally against your own dev server anyway:

```bash
cd selenium-tests
pip install -r requirements.txt
# Terminal 1
cd ../web && npm run dev
# Terminal 2
cd selenium-tests
BASE_URL=http://localhost:5173/nutriscan-ai/ python -m pytest -k test_auth_login_page --headed
```

`--headed` opens a real browser window instead of running headless.

---

## 7. Extending the suite

- New page → add a page object in `pages/` following the existing
  pattern (subclass `BasePage`, use `find_visible`/`click_visible` for
  anything inside `AppShell`).
- New test file → drop it in `tests/`, tag it with the closest existing
  `pytestmark` category (see `pytest.ini` for the registered markers),
  or add a new marker there if it's a genuinely new category.
- Before trusting any pass-rate number, grep for the anti-pattern this
  suite is built to avoid:
  ```bash
  grep -rn "or True\|assert True" selenium-tests/tests/
  ```
  (Should return nothing outside of comments.)
