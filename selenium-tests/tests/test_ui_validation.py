"""Category: UI Validation"""

import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.base_page import BasePage
import config


pytestmark = pytest.mark.ui


@pytest.fixture()
def guest_session(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return driver


PAGES = [
    ("", "home"),
    ("history", "history"),
    ("profile", "profile"),
    ("scan", "scan"),
    ("results/new", "results"),
]


class TestPageChrome:
    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_has_exactly_one_h1(self, driver, guest_session, route, name):
        page = BasePage(driver).open(route)
        page.wait_present(By.CSS_SELECTOR, "body")
        h1s = driver.find_elements(By.TAG_NAME, "h1")
        assert len(h1s) >= 1, f"{name} page has no <h1>"

    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_shows_top_bar_or_sidebar_brand(self, driver, guest_session, route, name):
        page = BasePage(driver).open(route)
        assert page.text_present("NutriScan", timeout=config.DEFAULT_TIMEOUT), (
            f"Brand name missing on {name} page"
        )

    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_title_set(self, driver, guest_session, route, name):
        BasePage(driver).open(route)
        assert driver.title.strip() != "", f"Empty <title> on {name} page"

    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_has_no_visible_untranslated_placeholder_text(self, driver, guest_session, route, name):
        """Catches leftover dev scaffolding like 'TODO', 'Lorem ipsum',
        '{{ }}' template artifacts, undefined/NaN leaking into the DOM."""
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "body")
        body_text = driver.find_element(By.TAG_NAME, "body").text
        for artifact in ("TODO", "Lorem ipsum", "undefined", "[object Object]", "NaN"):
            assert artifact not in body_text, f"Found dev artifact '{artifact}' on {name} page"

    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_has_html_lang_attribute(self, driver, guest_session, route, name):
        BasePage(driver).open(route)
        lang = driver.find_element(By.TAG_NAME, "html").get_attribute("lang")
        assert lang and lang.strip() != "", f"Missing <html lang> on {name} page"

    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_has_no_duplicate_element_ids(self, driver, guest_session, route, name):
        """Duplicate ids break `document.getElementById`, `#id` CSS
        selectors, and label `for=` associations — a real, common bug
        class in component-based UIs where a component gets reused."""
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "body")
        ids = driver.execute_script(
            "return Array.from(document.querySelectorAll('[id]')).map(e => e.id);"
        )
        duplicates = {i for i in ids if ids.count(i) > 1}
        assert not duplicates, f"Duplicate DOM ids on {name} page: {duplicates}"

    @pytest.mark.parametrize("route,name", PAGES)
    def test_no_severe_console_errors_on_page_load(self, driver, guest_session, route, name):
        BasePage(driver).open(route)
        severe = [
            entry for entry in driver.get_log("browser")
            if entry.get("level") == "SEVERE"
            and "favicon" not in entry.get("message", "").lower()
        ]
        assert not severe, f"Unexpected SEVERE console errors on {name} page: {severe}"

    @pytest.mark.parametrize("route,name", PAGES)
    def test_page_finishes_loading_within_reasonable_time(self, driver, guest_session, route, name):
        import time
        start = time.monotonic()
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "h1", timeout=config.DEFAULT_TIMEOUT)
        elapsed = time.monotonic() - start
        assert elapsed < config.DEFAULT_TIMEOUT, (
            f"{name} page took {elapsed:.1f}s to show an <h1> (limit {config.DEFAULT_TIMEOUT}s)"
        )


class TestMetaTags:
    def test_viewport_meta_tag_present(self, driver):
        LoginPage(driver).open_login()
        metas = driver.find_elements(By.CSS_SELECTOR, "meta[name='viewport']")
        assert metas, "No <meta name='viewport'> — required for correct mobile rendering"

    def test_charset_declared(self, driver):
        LoginPage(driver).open_login()
        charset_meta = driver.find_elements(By.CSS_SELECTOR, "meta[charset]")
        assert charset_meta, "No <meta charset> declared"

    def test_favicon_link_present(self, driver):
        LoginPage(driver).open_login()
        icons = driver.find_elements(By.CSS_SELECTOR, "link[rel*='icon']")
        assert icons, "No favicon <link rel='icon'> in document head"


class TestFormElementStates:
    def test_scan_barcode_submit_button_enabled_by_default(self, driver, guest_session):
        page = BasePage(driver).open("scan")
        btn = page.wait_visible(By.ID, "btn-scan-barcode")
        assert btn.is_enabled()

    def test_login_page_email_input_has_correct_type(self, driver):
        page = LoginPage(driver).open_login()
        page.reveal_email_form()
        field = page.wait_visible(*page.EMAIL_INPUT)
        assert field.get_attribute("type") == "email"

    def test_login_page_email_input_has_placeholder(self, driver):
        page = LoginPage(driver).open_login()
        page.reveal_email_form()
        field = page.wait_visible(*page.EMAIL_INPUT)
        assert (field.get_attribute("placeholder") or "").strip() != ""


class TestLinksAndButtonsAreInteractable:
    @pytest.mark.parametrize("element_id", [
        "btn-google-signin", "btn-email-signin", "btn-guest",
    ])
    def test_login_page_buttons_are_clickable_elements(self, driver, element_id):
        page = LoginPage(driver).open_login()
        el = page.wait_visible(By.ID, element_id)
        assert el.tag_name.lower() == "button"
        assert el.is_enabled()
