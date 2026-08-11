import pytest

from pages.login_page import LoginPage
from pages.results_page import ResultsPage
import config


pytestmark = pytest.mark.crud


@pytest.fixture()
def guest_session(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return driver


class TestResultsPageDirectAccess:
    def test_results_route_reachable_for_guest(self, driver, guest_session):
        """Navigating directly to /results/:id without router state (i.e.
        not arriving from a real scan submission) must not crash the app —
        this is exactly what happens on a bookmark, refresh, or shared
        link."""
        page = ResultsPage(driver).open_results("new")
        assert "results" in page.current_path()

    def test_results_page_does_not_produce_uncaught_error(self, driver, guest_session):
        from selenium.webdriver.common.by import By
        page = ResultsPage(driver).open_results("some-id-without-router-state")
        body_text = page.driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text

    def test_results_page_body_not_blank_without_router_state(self, driver, guest_session):
        from selenium.webdriver.common.by import By
        page = ResultsPage(driver).open_results("new")
        page.wait_present(By.TAG_NAME, "body")
        assert page.driver.find_element(By.TAG_NAME, "body").text.strip() != ""

    def test_results_page_survives_reload_without_router_state(self, driver, guest_session):
        from selenium.webdriver.common.by import By
        page = ResultsPage(driver).open_results("new")
        page.wait_present(By.TAG_NAME, "body")
        driver.refresh()
        page.wait_present(By.TAG_NAME, "body")
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text

    def test_results_page_nav_chrome_still_present(self, driver, guest_session):
        """Even a results page with nothing to show should keep the
        persistent AppShell around it (top bar / avatar), not render a
        bare, chrome-less error page."""
        from selenium.webdriver.common.by import By
        page = ResultsPage(driver).open_results("new")
        page.wait_present(By.TAG_NAME, "body")
        assert page.exists(By.ID, "btn-user-avatar")
