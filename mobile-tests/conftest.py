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
    time.sleep(2)
    # The relaunch above just handed the app a brand-new Dart isolate.
    # The existing Flutter-Driver session (created once for the whole
    # shard) is still wired to the isolate from before this force-stop
    # and will fail/timeout on every command from here on unless we
    # reconnect. This is the fix for the near-100% failure rate seen
    # when this reconnect was missing.
    driver.reconnect()
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
