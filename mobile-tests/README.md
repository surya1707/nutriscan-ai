# NutriScan AI — Android E2E Test Suite (Appium + Flutter Driver)

This is the mobile counterpart to `selenium-tests/` (the existing web
suite in this repo). It did not exist before this change — there was
no `mobile-tests/` folder, no `android-e2e` CI workflow, and no
ValueKeys on the Flutter widget tree.

## What's real right now vs. what needs a CI run

**Real, and true today:**
- 147 hand-written pytest test functions across 16 files, expanding to
  **450 collected test cases** via `@pytest.mark.parametrize` (verified
  by AST-parsing every file — see the count reproduced below). All 16
  files pass `python -m py_compile`.
- Every test addresses a real `ValueKey` added to the actual Flutter
  widget tree in `mobile/lib/` in this same change (auth buttons, bottom
  nav, scan/gallery/flash controls, history rows, profile chips, etc).
- The full framework: page objects, a two-tier-timeout driver wrapper,
  adb-based replacements for the three Flutter-driver commands that
  don't work on this engine version, a report generator that produces
  the same 6-sheet `Automation_Test_Report.xlsx` schema as the existing
  `selenium-tests/`, a pass-rate gate script, and a GitHub Actions
  workflow (`.github/workflows/android-e2e.yml`) that builds the debug
  APK, runs all 4 shards on emulators, and merges the results.

**Not real yet, and I'm not going to pretend otherwise:**
- **No test has actually been executed.** I have no Android emulator,
  no Appium server, and no display in the environment I built this in
  — there was no way to run these tests here, and fabricating a
  "PASSED: 447/450" report for a final-year project would be
  misrepresenting results that don't exist. That's not something I'll
  do, especially for something you'll submit for evaluation.
- `mobile-tests/reports/Test-Plan-400-Cases.xlsx` is a **test plan**,
  not an execution report — every row's Status column says
  `Not Executed`. It documents what each test does; it does not claim
  any of them ran.
- The **real** `Automation_Test_Report.xlsx` (matching your friend's
  sample format, and the one already in this repo at
  `docs/Automation_Test_Report.xlsx` for the web suite) gets generated
  automatically — with genuine Pass/Fail/Duration data — the first time
  `.github/workflows/android-e2e.yml` actually runs on GitHub's
  macOS emulator runners. Push this branch, or trigger the workflow
  manually from the Actions tab, and download it from the
  `Automation_Test_Report` artifact when the run finishes (typically
  20-35 minutes across 4 shards).

If you need that real report before a deadline, running the workflow
is the next step — I can also walk you through interpreting any
failures it turns up once you have it.

## Stack detection (what this suite is built against)

| Question | Finding | Evidence |
|---|---|---|
| Framework | Flutter, Dart SDK `>=3.0.0 <4.0.0` | `mobile/pubspec.yaml` |
| Router | `go_router ^13.0.0` | `mobile/lib/core/router/app_router.dart` |
| Auth | Firebase Auth — Google, email-link, or Guest. No password login. | `mobile/lib/features/auth/` |
| Package id (debug) | `com.example.nutriscan` | `mobile/android/app/build.gradle.kts` |
| Local persistence | Drift (SQLite) — scan history + profile stored on-device | `mobile/lib/core/database/` |
| Backend calls in critical path | None — OCR is on-device (`google_mlkit_text_recognition`) | `mobile/lib/features/scanner/` |
| Push notifications | **Not implemented** — no `firebase_messaging` dependency | `mobile/pubspec.yaml` (grepped, absent) |
| Search / filter bar | **Not implemented** — no search or filter UI anywhere in the app | grepped `mobile/lib` for "search"/"filter" |
| Orientation | Portrait-locked | `SystemChrome.setPreferredOrientations([...portraitUp])` in `main.dart` |
| Bottom nav | Classic Material 2 `BottomNavigationBar` (single label per tab) | `mobile/lib/shared/widgets/main_shell.dart` — **not** the Material 3 dual-label crossfade some other Flutter apps use |

Where the original task brief assumed a category that doesn't apply
here (Registration, push Notifications, Search, Filters — see the
"Coverage honesty note" at the top of the corresponding test files),
I substituted the closest thing the app actually has, rather than
writing tests against UI that isn't there.

## Layout

```
mobile-tests/
├── config.py                  # capabilities, timeouts, test data, route markers
├── conftest.py                 # session driver fixture, reset_to_guest_home, result recording
├── driver_wrapper.py           # two-tier AppiumConnection timeout wrapper
├── pytest.ini
├── requirements.txt
├── pages/                      # one page object per screen
├── tests/                      # 16 files, 450 collected test cases (see table below)
├── utils/adb_helpers.py        # adb replacements for unsupported Flutter Driver commands
├── scripts/
│   ├── key_audit.py             # flags interactive widgets still missing a ValueKey
│   ├── generate_reports.py      # -> Automation_Test_Report.xlsx, summary.md, execution-results.json
│   └── check_pass_rate.py       # CI gate, run AFTER artifacts are uploaded
└── reports/
    └── Test-Plan-400-Cases.xlsx # the 450-row test PLAN (Status = Not Executed)
```

## Test case count by category

| File | Category | Test functions | Collected cases (incl. parametrize) |
|---|---|---:|---:|
| test_authentication.py | Authentication | 21 | 45 |
| test_authorization.py | Authorization / Route Guards | 11 | 32 |
| test_navigation.py | Navigation | 11 | 30 |
| test_home_dashboard.py | Dashboard / Home | 10 | 21 |
| test_forms.py | Forms | 11 | 37 |
| test_scan_history_crud.py | CRUD (Scan History) | 9 | 39 |
| test_list_browsing_and_filters.py | List Browsing & Filters | 7 | 34 |
| test_input_validation.py | Input Validation | 5 | 39 |
| test_error_handling.py | Error Handling | 7 | 24 |
| test_session_management.py | Session Management | 8 | 22 |
| test_inapp_messaging.py | In-App Messaging (SnackBars) | 5 | 20 |
| test_camera_file_upload.py | Camera & File Upload | 10 | 26 |
| test_offline_handling.py | Offline Handling | 7 | 21 |
| test_accessibility.py | Accessibility | 8 | 20 |
| test_responsive_ui.py | Responsive UI | 6 | 10 |
| test_profile_management.py | Profile Management | 11 | 30 |
| **Total** | | **147** | **450** |

Reproduce this table yourself:

```bash
cd mobile-tests
python3 -m pytest --collect-only -q tests/ | tail -1
```

## Running it for real

You need: a machine (or CI runner) with an Android emulator or device,
Appium 2 + the `uiautomator2` driver, and Flutter installed.

```bash
# 1. Build the debug APK from the TEST entrypoint (not main.dart)
cd mobile
flutter pub get
flutter build apk --debug -t lib/main_test.dart

# 2. Start Appium
appium --base-path / &

# 3. Install deps and run
cd ../mobile-tests
pip install -r requirements.txt
export APK_PATH="$(pwd)/../mobile/build/app/outputs/flutter-apk/app-debug.apk"
python -m pytest tests/ -v --reruns 1 --reruns-delay 3

# 4. Generate the real report
python scripts/generate_reports.py
python scripts/check_pass_rate.py   # exits non-zero if pass rate < 95%
```

Or just push to `main` / open a PR touching `mobile/` or
`mobile-tests/` — `.github/workflows/android-e2e.yml` does all of the
above automatically and uploads `Automation_Test_Report.xlsx` as a
downloadable artifact.

## Gotchas discovered while building this (confirmed, not assumed)

- **`AppiumClientConfig` doesn't exist** in `Appium-Python-Client==3.1.1`
  — importing it kills the whole shard's collection. The working fix is
  `AppiumConnection.set_timeout(seconds)`, applied once at import time
  in `driver_wrapper.py`, with a temporary bump around `new_session()`
  only (Flutter's Observatory handshake can be slow on a cold emulator).
- **`driver.background_app()`, `set_network_connection()`, and
  `mobile: scrollGesture`** are not supported / return HTTP 500 against
  this app's Flutter engine + `appium-flutter-driver` combination — all
  three are replaced with direct `adb shell` calls in `utils/adb_helpers.py`.
- **No `page_source`, no route inspection API.** "Which screen am I on"
  is answered via a visible-text marker per screen
  (`config.ROUTE_TEXT_MARKERS`), not a URL/route check.
- **`.text` only resolves for `Text`/`EditableText` widgets.** Every
  other control (IconButton, GestureDetector, Container...) is checked
  with `is_displayed_by_key()`, never `.text` — this is why every
  interactive control got an explicit `key: const ValueKey('...')` in
  `mobile/lib/` as part of this change, rather than relying on text
  matching everywhere.
- This app's `BottomNavigationBar` is classic Material 2 (single label
  per tab). If you've worked with a Material 3 `NavigationBar`
  elsewhere, note the dual-label crossfade bug that affects those
  **does not apply here** — confirmed by reading `main_shell.dart`, not
  assumed by analogy.

## App-side changes made to support this suite

- `mobile/lib/main_test.dart` — a test-only entrypoint that calls
  `enableFlutterDriverExtension()` then boots the exact same widget
  tree as `main.dart`. **`main.dart` itself was not touched.**
- `mobile/pubspec.yaml` — added `flutter_driver` under `dev_dependencies`.
- `key: const ValueKey('...')` added to ~35 interactive widgets across
  `auth_screen.dart`, `main_shell.dart`, `home_screen.dart`,
  `scanner_screen.dart`, `results_screen.dart`, `history_screen.dart`,
  and `profile_screen.dart`. Run `python scripts/key_audit.py` for the
  current list of interactive widgets that still don't have one —
  there are 22 remaining (mostly in the results/scanner detail widgets,
  which are reachable but not yet exercised by this first pass of the
  suite).
