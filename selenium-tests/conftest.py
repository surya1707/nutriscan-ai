"""
Shared pytest fixtures and hooks for the NutriScan AI Selenium suite.

Design notes (each one fixes a specific class of pain, not a hypothetical):

- Driver creation uses Selenium 4.6+'s built-in Selenium Manager (no
  webdriver-manager / manual chromedriver download). In CI, `CHROME_PATH`
  is read from the environment if set (browser-actions/setup-chrome
  outputs it) and passed as opts.binary_location.
- Screenshot filenames are sanitized (strip \\/*?:"<>|) before writing —
  GitHub Actions' artifact upload silently drops files with illegal
  characters, which makes failures impossible to debug after the fact.
- Result collection is written to a PER-WORKER file
  (reports/results/result_<worker>.json). This file is never touched by
  more than one process, so there is no xdist race. A separate step
  (scripts/generate_reports.py) globs and merges all worker files after
  the full pytest run has finished — never inside a pytest hook, because
  pytest-xdist workers finish at different times and hooks would race
  each other for the merged file.
- No `time.sleep()` here or anywhere in this suite. All waits are
  WebDriverWait + expected_conditions.
"""

import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Imported as `app_config`, NOT `config` — pytest's own hookspecs use a
# parameter literally named `config` (see pytest_configure below), and
# pluggy validates hookimpl signatures by parameter name. A bare
# `import config` here would force every hook that needs pytest's config
# object to shadow this module, so every other file in this project uses
# `import config` while conftest.py alone aliases it.
import config as app_config

os.makedirs(app_config.RESULTS_DIR, exist_ok=True)
os.makedirs(app_config.SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(app_config.LOGS_DIR, exist_ok=True)

# ── Logging ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(app_config.LOGS_DIR, "selenium-tests.log")),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("nutriscan.selenium")


def _sanitize(name: str) -> str:
    """Strip characters that break filesystem paths / GH Actions artifact upload."""
    return re.sub(r'[\\/*?:"<>|]', "_", name)


def _worker_id(config_obj) -> str:
    """'master' when run without xdist, otherwise e.g. 'gw0'."""
    return os.environ.get("PYTEST_XDIST_WORKER", "master")


# ── CLI options ─────────────────────────────────────────────────────────
def pytest_addoption(parser):
    parser.addoption("--base-url", action="store", default=None, help="Override BASE_URL")
    parser.addoption("--headed", action="store_true", default=False, help="Run with a visible browser window")


def pytest_configure(config):
    base_url = config.getoption("--base-url")
    if base_url:
        app_config.BASE_URL = base_url.rstrip("/") + "/"
    if config.getoption("--headed"):
        app_config.HEADLESS = False

    config._nutriscan_worker = _worker_id(config)
    config._nutriscan_results = []
    logger.info("Target BASE_URL = %s (headless=%s, worker=%s)",
                app_config.BASE_URL, app_config.HEADLESS, config._nutriscan_worker)


# ── Driver fixture ──────────────────────────────────────────────────────
@pytest.fixture()
def driver(request):
    options = Options()
    if app_config.HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    # Firebase's Google sign-in popup would otherwise hang a headless
    # session forever; nothing in this suite completes that flow, but a
    # stray click shouldn't be able to wedge a worker.
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

    chrome_path = os.environ.get("CHROME_PATH")
    if chrome_path:
        options.binary_location = chrome_path

    drv = webdriver.Chrome(options=options)
    drv.implicitly_wait(0)  # explicit waits only — see module docstring
    drv.set_page_load_timeout(30)

    yield drv

    drv.quit()


@pytest.fixture()
def base_url():
    return app_config.BASE_URL


# ── Screenshot + browser-console log capture on failure ────────────────
@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)

    if report.when == "call" and report.failed:
        drv = item.funcargs.get("driver")
        if drv is not None:
            shot_name = _sanitize(f"{item.nodeid}") + ".png"
            shot_path = os.path.join(app_config.SCREENSHOTS_DIR, shot_name)
            try:
                drv.save_screenshot(shot_path)
                logger.info("Saved failure screenshot: %s", shot_path)
            except Exception as exc:  # noqa: BLE001 - best-effort diagnostics
                logger.warning("Could not save screenshot for %s: %s", item.nodeid, exc)

            try:
                console_logs = drv.get_log("browser")
                if console_logs:
                    log_name = _sanitize(f"{item.nodeid}") + ".console.log"
                    with open(os.path.join(app_config.LOGS_DIR, log_name), "w", encoding="utf-8") as fh:
                        for entry in console_logs:
                            fh.write(f"{entry}\n")
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not capture browser console for %s: %s", item.nodeid, exc)


# ── Per-test result collection (xdist-safe: one file per worker) ───────
def pytest_runtest_logreport(report):
    if report.when != "call" and not (report.when == "setup" and report.outcome != "passed"):
        return

    status = report.outcome  # "passed" | "failed" | "skipped"
    entry = {
        "nodeid": report.nodeid,
        "status": status,
        "duration_s": round(getattr(report, "duration", 0.0), 3),
        "module": report.nodeid.split("::")[0],
        "longrepr": str(report.longrepr) if status == "failed" else None,
    }
    pytest.__nutriscan_pending = getattr(pytest, "__nutriscan_pending", [])
    pytest.__nutriscan_pending.append(entry)


def pytest_sessionfinish(session, exitstatus):
    worker = _worker_id(session.config)
    pending = getattr(pytest, "__nutriscan_pending", [])

    out_path = os.path.join(app_config.RESULTS_DIR, f"result_{worker}.json")
    payload = {
        "worker": worker,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": app_config.BASE_URL,
        "results": pending,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    logger.info("Wrote %d result(s) to %s", len(pending), out_path)
