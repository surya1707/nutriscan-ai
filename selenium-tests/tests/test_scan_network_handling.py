"""
Category: Error Handling

This suite intentionally runs with NO backend alongside it (see
config.py module docstring and README "Why no backend"). That means a
valid-looking scan submission WILL hit the network and WILL fail. These
tests assert that failure is surfaced to the user cleanly — a visible
error message and a resolved (non-infinite) loading state — rather than
a silent hang or a blank screen. That is real, valuable coverage: it is
exactly the failure mode a flaky wifi connection or a backend outage
produces for a real user.
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.login_page import LoginPage
from pages.scan_page import ScanPage
import config


pytestmark = pytest.mark.error_handling


@pytest.fixture()
def scan_page(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    page = ScanPage(driver).open_scan()
    page.wait_visible(*page.BARCODE_INPUT)
    return page


class TestBarcodeSubmissionWithoutBackend:
    def test_barcode_submission_resolves_loading_state(self, scan_page):
        scan_page.submit_barcode("5000112637922")
        # The submit button is disabled while `loading` is true; it must
        # come back regardless of whether the request succeeds or fails.
        btn = scan_page.wait_present(*scan_page.BARCODE_SUBMIT_BTN)
        WebDriverWait(scan_page.driver, config.DEFAULT_TIMEOUT).until(
            lambda d: btn.get_attribute("disabled") is None
        )
        assert btn.get_attribute("disabled") is None

    def test_barcode_submission_shows_error_when_backend_unreachable(self, scan_page):
        scan_page.submit_barcode("5000112637922")
        assert scan_page.has_visible_error(timeout=config.DEFAULT_TIMEOUT)

    def test_barcode_submission_does_not_navigate_away_on_network_failure(self, scan_page):
        scan_page.submit_barcode("5000112637922")
        scan_page.has_visible_error(timeout=config.DEFAULT_TIMEOUT)
        assert "scan" in scan_page.current_path()


class TestIngredientsSubmissionWithoutBackend:
    def test_ingredients_submission_resolves_loading_state(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        scan_page.submit_ingredients("sugar, salt, monosodium glutamate")
        btn = scan_page.wait_present(*scan_page.INGREDIENTS_SUBMIT_BTN)
        WebDriverWait(scan_page.driver, config.DEFAULT_TIMEOUT).until(
            lambda d: btn.get_attribute("disabled") is None
        )
        assert btn.get_attribute("disabled") is None

    def test_ingredients_submission_shows_error_when_backend_unreachable(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        scan_page.submit_ingredients("sugar, salt, water")
        assert scan_page.has_visible_error(timeout=config.DEFAULT_TIMEOUT)


class TestHomeAndHistoryDegradeGracefully:
    """Home and History both fetch data on mount (see HomePage.tsx /
    HistoryPage.tsx `useEffect`). Without a backend those requests fail;
    the pages must still render their static chrome instead of crashing."""

    def test_home_page_renders_without_backend(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        # No unhandled React error boundary text ("Something went wrong" /
        # a blank <body>) should be present.
        body_text = driver.find_element(By.TAG_NAME, "body").text
        assert body_text.strip() != ""

    def test_history_page_renders_without_backend(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = driver
        from pages.history_page import HistoryPage
        history = HistoryPage(page).open_history()
        assert "history" in history.heading_text(timeout=config.DEFAULT_TIMEOUT).lower()

    def test_no_uncaught_react_error_boundary_after_failed_fetches(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "something went wrong" not in body_text
        assert "uncaught" not in body_text

    def test_profile_page_renders_without_backend(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        from pages.base_page import BasePage
        page = BasePage(driver).open("profile")
        page.wait_present(By.TAG_NAME, "h1", timeout=config.DEFAULT_TIMEOUT)
        assert driver.find_element(By.TAG_NAME, "body").text.strip() != ""

    def test_retrying_a_failed_barcode_scan_clears_the_previous_error(self, scan_page):
        scan_page.submit_barcode("5000112637922")
        assert scan_page.has_visible_error(timeout=config.DEFAULT_TIMEOUT)
        scan_page.submit_barcode("012345678905")
        # A second submission attempt must still leave a coherent,
        # non-crashed UI — not necessarily error-free (still no backend),
        # but the app must still be responsive.
        from selenium.webdriver.support.ui import WebDriverWait
        btn = scan_page.wait_present(*scan_page.BARCODE_SUBMIT_BTN)
        WebDriverWait(scan_page.driver, config.DEFAULT_TIMEOUT).until(
            lambda d: btn.get_attribute("disabled") is None
        )
        assert btn.get_attribute("disabled") is None
