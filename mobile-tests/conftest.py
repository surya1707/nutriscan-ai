"""
Shared pytest fixtures for the mobile-tests suite.

Design notes:
  - One Appium session per test FILE (function-scoped would be far too
    slow — cold Flutter Driver handshakes on this app take 8-15s each).
    Each test starts from a known state via `reset_to_guest_home`
    rather than a fresh driver, mirroring the pattern used in
    selenium-tests/conftest.py for the web suite.
  - `execution-results.json` is appended to after every test so
    scripts/generate_reports.py can build the xlsx/html report even if
    a later test in the shard crashes the process.
"""

import json
import os
import time

import pytest

import config
from appium_flutter_finder.flutter_finder import FlutterFinder
from driver_wrapper import DriverProxy, new_driver, quit_driver
from pages.auth_page import AuthPage
from pages.history_page import HistoryPage
from pages.home_page import HomePage
from pages.main_shell_page import MainShellPage
from pages.profile_page import ProfilePage
from pages.results_page import ResultsPage
from pages.scanner_page import ScannerPage
from utils import adb_helpers

RESULTS_PATH = os.path.join(config.REPORTS_DIR, "raw-results.jsonl")

_OBSERVATORY_PROBE_TIMEOUT = 35  # seconds — safely above the ~16 s dead zone


def _wait_for_driver_ready(driver, timeout: int = _OBSERVATORY_PROBE_TIMEOUT) -> None:
    """Block until the Dart VM Observatory responds to a flutter:waitFor
    round-trip, or until `timeout` seconds elapse.

    After every adb force-stop + relaunch + driver.reconnect(), there is a
    ~15-16 s window during which the Observatory is reachable but every
    flutter:waitFor call returns a timeout error — the Dart VM is alive
    (session was created) but busy with Impeller GPU init and the Drift
    background isolate startup. Using a blind time.sleep() here means the
    dead-zone cost comes straight out of the *test's* timeout budget; using
    an active poll here means the harness waits exactly as long as needed
    (no more, no less) before the test starts.

    'NutriScan AI' is the MaterialApp title — it is always present in the
    Flutter widget tree immediately after cold start, on every screen, so it
    is safe to use as a liveness probe without caring which screen the app
    lands on after relaunch.
    """
    probe = FlutterFinder().by_text("NutriScan AI")
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            # 3 000 ms sub-timeout matches wait_for_key/wait_for_text so
            # each loop iteration costs at most 3 s + a tiny round-trip
            # overhead rather than returning immediately on a timeout error.
            driver.execute_script("flutter:waitFor", probe, 3000)
            return  # Observatory is live — hand off to the test
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    # If we reach here the app may be unusually slow to start; don't raise —
    # let the test's own wait_for_* produce the failure with a specific,
    # meaningful widget-level message rather than a generic readiness error.


def pytest_addoption(parser):
    parser.addoption(
        "--shard-name", action="store", default="default",
        help="Logical shard name, recorded in execution-results.json",
    )


@pytest.fixture(scope="session")
def driver():
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(config.LOGS_DIR, exist_ok=True)
    # Wrapped in DriverProxy (not the raw webdriver) so that any fixture
    # or test that force-stops/relaunches the app via raw adb can call
    # `driver.reconnect()` afterwards and get a session bound to the new
    # process's Dart isolate, instead of silently continuing to talk to
    # a killed one. See DriverProxy's docstring in driver_wrapper.py.
    proxy = DriverProxy(new_driver())
    # Belt-and-suspenders alongside the `appium:autoGrantPermissions`
    # capability in driver_wrapper.py: the previous CI run showed
    # test_camera_file_upload.py still failing 0/25 and most of
    # test_inapp_messaging.py still failing after that capability was
    # added, with counts essentially unchanged from before the fix — so
    # either the patch didn't land as expected, or the capability isn't
    # being honored end-to-end through appium-flutter-driver's UiAutomator2
    # passthrough. Rather than debug that capability further, grant the
    # permission directly via adb, which is the exact mechanism the two
    # explicit-permission tests already rely on and is proven to work.
    adb_helpers.grant_camera_permission()
    yield proxy
    quit_driver(proxy._driver)


@pytest.fixture
def auth_page(driver):
    return AuthPage(driver)


@pytest.fixture
def main_shell(driver):
    return MainShellPage(driver)


@pytest.fixture
def home_page(driver):
    return HomePage(driver)


@pytest.fixture
def scanner_page(driver):
    return ScannerPage(driver)


@pytest.fixture
def results_page(driver):
    return ResultsPage(driver)


@pytest.fixture
def history_page(driver):
    return HistoryPage(driver)


@pytest.fixture
def profile_page(driver):
    return ProfilePage(driver)


@pytest.fixture
def reset_to_guest_home(driver, auth_page, home_page):
    """Force-stop + relaunch, then get to a signed-in-as-guest Home
    screen, tolerating whichever of the two possible cold-start states
    (Auth screen vs. already-persisted guest session) the app is in."""
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    # Re-grant in case a prior test in this shard called clear_app_data()
    # (pm clear resets all runtime permission grants, camera included).
    # Idempotent/cheap when already granted, so safe to run unconditionally
    # before every test rather than trying to track which earlier test
    # might have cleared data.
    adb_helpers.grant_camera_permission()
    # Short pause so the adb-relaunched process is accepting connections
    # before we open a new Appium session against it.
    time.sleep(1)
    # The relaunch above just handed the app a brand-new Dart isolate.
    # The existing Flutter-Driver session (created once for the whole
    # shard) is still wired to the isolate from before this force-stop
    # and will fail/timeout on every command from here on unless we
    # reconnect. This is the fix for the near-100% failure rate seen
    # when this reconnect was missing.
    driver.reconnect()
    # Active Observatory ready-poll: block here until the Dart VM responds
    # to a flutter:waitFor round-trip. This absorbs the full ~15-16 s
    # cold-start dead zone (Impeller GPU init + Drift background isolate
    # startup) before the test starts, so the test's own timeout budget is
    # never consumed by infrastructure latency. Replaces the previous
    # blind time.sleep(2) which was too short by an order of magnitude.
    _wait_for_driver_ready(driver)
    try:
        if auth_page.is_loaded():
            auth_page.continue_as_guest()
    except Exception:
        pass
    home_page.is_loaded()
    return home_page


@pytest.fixture(autouse=True)
def _record_result(request):
    start = time.time()
    outcome = {"status": "unknown"}
    yield outcome
    duration = round(time.time() - start, 2)
    entry = {
        "test_id": request.node.nodeid,
        "name": request.node.name,
        "module": request.node.module.__name__ if request.node.module else "",
        "shard": request.config.getoption("--shard-name"),
        "duration_s": duration,
        "status": outcome.get("status", "unknown"),
        "doc": (request.node.function.__doc__ or "").strip() if hasattr(request.node, "function") else "",
    }
    os.makedirs(config.REPORTS_DIR, exist_ok=True)
    with open(RESULTS_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def pytest_runtest_makereport(item, call):
    if call.when != "call":
        return
    outcome_fixture = item.funcargs.get("_record_result")
    if outcome_fixture is None:
        return
    if call.excinfo is None:
        outcome_fixture["status"] = "passed"
    else:
        outcome_fixture["status"] = "failed"
        # best-effort failure screenshot + logcat
        driver = item.funcargs.get("driver")
        if driver is not None:
            try:
                from pages.base_page import BasePage
                BasePage(driver).capture_failure(item.name)
            except Exception:
                pass
