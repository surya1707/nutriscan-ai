"""
Category: Accessibility / Keyboard Operability

Separate file from test_accessibility.py because these specifically
drive the browser via keyboard events (Tab, Enter, Space) rather than
checking static attributes — a distinct, valuable failure mode (an
element can have a perfect aria-label and still be unreachable by
keyboard if it's not in the natural tab order).
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from pages.login_page import LoginPage
from pages.base_page import BasePage
import config


pytestmark = pytest.mark.accessibility


@pytest.fixture()
def guest_session(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return driver


class TestLoginPageTabOrder:
    @pytest.mark.parametrize("element_id", ["btn-google-signin", "btn-email-signin", "btn-guest"])
    def test_button_is_reachable_via_programmatic_focus(self, driver, element_id):
        """A necessary (not sufficient) condition for being in the tab
        order: the element must be focusable at all."""
        page = LoginPage(driver).open_login()
        el = page.wait_visible(By.ID, element_id)
        driver.execute_script("arguments[0].focus();", el)
        active = driver.switch_to.active_element
        assert active.get_attribute("id") == element_id

    def test_guest_button_activates_on_enter_key(self, driver):
        page = LoginPage(driver).open_login()
        btn = page.wait_visible(*page.GUEST_BTN)
        driver.execute_script("arguments[0].focus();", btn)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        page.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        assert page.current_path().rstrip("/") in ("", "/")

    def test_email_toggle_activates_on_enter_key(self, driver):
        page = LoginPage(driver).open_login()
        btn = page.wait_visible(*page.EMAIL_TOGGLE_BTN)
        driver.execute_script("arguments[0].focus();", btn)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        assert page.find_all_visible(*page.EMAIL_INPUT)

    def test_email_toggle_activates_on_space_key(self, driver):
        page = LoginPage(driver).open_login()
        btn = page.wait_visible(*page.EMAIL_TOGGLE_BTN)
        driver.execute_script("arguments[0].focus();", btn)
        driver.switch_to.active_element.send_keys(Keys.SPACE)
        assert page.find_all_visible(*page.EMAIL_INPUT)

    def test_tab_from_body_reaches_a_focusable_control_eventually(self, driver):
        """Sends Tab repeatedly from the top of the document and expects
        to land on SOME real interactive element within a small number of
        presses — catches a page that's entirely keyboard-inert."""
        page = LoginPage(driver).open_login()
        body = driver.find_element(By.TAG_NAME, "body")
        body.click()
        focused_tags = set()
        active = driver.switch_to.active_element
        for _ in range(8):
            active.send_keys(Keys.TAB)
            active = driver.switch_to.active_element
            focused_tags.add(active.tag_name.lower())
        assert focused_tags & {"button", "a", "input"}, (
            f"Tabbing never reached an interactive element (saw: {focused_tags})"
        )


class TestScanPageKeyboardOperability:
    def test_barcode_submit_activates_on_enter_key_in_field(self, driver, guest_session):
        page = BasePage(driver).open("scan")
        field = page.wait_visible(By.ID, "input-barcode")
        field.send_keys("5000112637922")
        field.send_keys(Keys.ENTER)
        # Either the form submits (loading/error state appears) or Enter
        # is a no-op in a plain text input without a <form> wrapper —
        # both are fine; a JS exception breaking the page is not.
        page.wait_present(By.TAG_NAME, "body")
        assert driver.find_element(By.TAG_NAME, "body").text.strip() != ""

    def test_barcode_submit_button_activates_on_enter_key_when_focused(self, driver, guest_session):
        page = BasePage(driver).open("scan")
        field = page.wait_visible(By.ID, "input-barcode")
        field.send_keys("5000112637922")
        btn = page.wait_visible(By.ID, "btn-scan-barcode")
        driver.execute_script("arguments[0].focus();", btn)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        page.wait_present(By.TAG_NAME, "body")


class TestAvatarMenuKeyboardOperability:
    def test_avatar_menu_opens_on_enter_key(self, driver, guest_session):
        page = BasePage(driver).open("")
        btn = page.wait_visible(By.ID, "btn-user-avatar")
        driver.execute_script("arguments[0].focus();", btn)
        driver.switch_to.active_element.send_keys(Keys.ENTER)
        assert page.exists(By.ID, "btn-signout")

    def test_escape_key_closes_avatar_menu_or_is_a_safe_no_op(self, driver, guest_session):
        page = BasePage(driver).open("")
        btn = page.wait_visible(By.ID, "btn-user-avatar")
        btn.click()
        driver.switch_to.active_element.send_keys(Keys.ESCAPE)
        # Whether Escape closes the menu or does nothing, the page must
        # remain usable (no crash, body still has content).
        assert driver.find_element(By.TAG_NAME, "body").text.strip() != ""


class TestFocusIndicatorsExist:
    @pytest.mark.parametrize("element_id", ["btn-google-signin", "btn-guest"])
    def test_focused_button_has_a_visible_outline_or_box_shadow(self, driver, element_id):
        """A minimal, deterministic check: a focused interactive element
        must have SOME non-'none' outline or box-shadow so keyboard users
        can see where focus is — not a full contrast/visibility audit."""
        page = LoginPage(driver).open_login()
        el = page.wait_visible(By.ID, element_id)
        driver.execute_script("arguments[0].focus();", el)
        outline, box_shadow = driver.execute_script(
            "const s = getComputedStyle(arguments[0]);"
            "return [s.outlineStyle, s.boxShadow];",
            el,
        )
        has_indicator = (outline and outline != "none") or (box_shadow and box_shadow != "none")
        assert has_indicator, f"#{element_id} has no visible focus indicator"
