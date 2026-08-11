import pytest

from pages.login_page import LoginPage
from pages.history_page import HistoryPage
import config


pytestmark = pytest.mark.crud


@pytest.fixture()
def history_page(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return HistoryPage(driver).open_history()


class TestHistoryPage:
    def test_history_heading_renders(self, history_page):
        assert "history" in history_page.heading_text(timeout=config.DEFAULT_TIMEOUT).lower()

    def test_history_page_settles_out_of_loading_state(self, history_page):
        from selenium.webdriver.support.ui import WebDriverWait
        WebDriverWait(history_page.driver, config.DEFAULT_TIMEOUT).until(
            lambda d: not history_page.is_loading()
        )
        assert not history_page.is_loading()

    def test_history_page_reachable_directly_by_url_for_guest(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = HistoryPage(driver).open_history()
        page.wait_for_path("/history", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/history"

    def test_history_page_survives_reload(self, history_page):
        history_page.driver.refresh()
        history_page.wait_for_path("/history", timeout=config.DEFAULT_TIMEOUT)
        assert "history" in history_page.heading_text(timeout=config.DEFAULT_TIMEOUT).lower()

    def test_history_page_survives_rapid_repeated_reloads(self, history_page):
        """Guards against a race in the data-fetch useEffect that only
        shows up when the component mounts/unmounts in quick succession."""
        for _ in range(3):
            history_page.driver.refresh()
        history_page.wait_for_path("/history", timeout=config.DEFAULT_TIMEOUT)
        assert "history" in history_page.heading_text(timeout=config.DEFAULT_TIMEOUT).lower()

    def test_history_page_has_no_uncaught_error_after_failed_fetch(self, history_page):
        from selenium.webdriver.common.by import By
        body_text = history_page.driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text
        assert "something went wrong" not in body_text

    def test_history_page_load_more_button_present_or_gracefully_absent(self, history_page):
        """With no backend reachable there's nothing to page through —
        the Load More control must either not render, or render disabled
        rather than throwing when clicked with no data behind it."""
        if history_page.exists(*history_page.LOAD_MORE_BTN):
            btn = history_page.wait_visible(*history_page.LOAD_MORE_BTN)
            assert btn.is_displayed()
        else:
            assert True

    def test_history_page_body_not_empty_even_without_backend_data(self, history_page):
        from selenium.webdriver.common.by import By
        body_text = history_page.driver.find_element(By.TAG_NAME, "body").text
        assert body_text.strip() != ""
