import pytest

from pages.login_page import LoginPage
from pages.profile_page import ProfilePage
import config


pytestmark = pytest.mark.crud


@pytest.fixture()
def profile_page(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return ProfilePage(driver).open_profile()


class TestProfilePage:
    def test_profile_heading_renders(self, profile_page):
        assert profile_page.wait_visible(*profile_page.HEADING, timeout=config.DEFAULT_TIMEOUT)

    def test_profile_signout_button_present(self, profile_page):
        assert profile_page.exists(*profile_page.SIGNOUT_BTN)

    def test_profile_signout_redirects_to_login(self, profile_page):
        profile_page.sign_out()
        profile_page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert profile_page.current_path().rstrip("/") == "/login"

    def test_display_name_field_accepts_input(self, profile_page):
        if not profile_page.exists(*profile_page.DISPLAY_NAME_INPUT):
            pytest.skip("Display-name field not present for this auth state")
        profile_page.set_display_name("QA Selenium Runner")
        field = profile_page.wait_visible(*profile_page.DISPLAY_NAME_INPUT)
        assert field.get_attribute("value") == "QA Selenium Runner"

    def test_profile_reachable_directly_by_url_for_guest(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = ProfilePage(driver).open_profile()
        page.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/profile"

    def test_profile_page_survives_reload(self, profile_page):
        profile_page.driver.refresh()
        profile_page.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)
        assert profile_page.exists(*profile_page.HEADING)

    def test_profile_page_no_uncaught_error_after_failed_fetch(self, profile_page):
        from selenium.webdriver.common.by import By
        body_text = profile_page.driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text

    @pytest.mark.parametrize("name_value", [
        "A" * 100,               # long name
        "O'Brien-Smith",         # apostrophe + hyphen
        "名前",                    # non-Latin script
        "  leading and trailing  ",
        "<script>alert(1)</script>",
    ])
    def test_display_name_field_accepts_various_inputs_without_crashing(self, profile_page, name_value):
        if not profile_page.exists(*profile_page.DISPLAY_NAME_INPUT):
            pytest.skip("Display-name field not present for this auth state")
        profile_page.set_display_name(name_value)
        field = profile_page.wait_visible(*profile_page.DISPLAY_NAME_INPUT)
        assert field.get_attribute("value") == name_value
