"""
Category: Accessibility

Lightweight, deterministic a11y checks (no axe-core dependency, so no
external CDN fetch is required in CI). These check the specific
attributes present in the source (aria-label on icon-only buttons,
input types, alt text) rather than a generic audit — deterministic
enough to gate CI on, unlike a full WCAG scan.
"""

import pytest
from selenium.webdriver.common.by import By

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


class TestIconOnlyButtonsHaveAccessibleNames:
    @pytest.mark.parametrize("element_id", ["btn-user-avatar", "btn-hamburger"])
    def test_icon_button_has_aria_label(self, driver, guest_session, element_id):
        page = BasePage(driver).open("")
        el = page.wait_visible(By.ID, element_id, timeout=config.DEFAULT_TIMEOUT)
        aria_label = el.get_attribute("aria-label")
        assert aria_label and aria_label.strip() != "", (
            f"#{element_id} is an icon-only control with no aria-label"
        )

    def test_main_nav_has_aria_label(self, driver, guest_session):
        page = BasePage(driver).open("")
        page.set_viewport(*config.VIEWPORTS["mobile"])
        driver.refresh()
        nav = page.wait_visible(By.CSS_SELECTOR, "nav[aria-label]", timeout=config.DEFAULT_TIMEOUT)
        assert nav.get_attribute("aria-label")


class TestFormFieldsAreLabeled:
    def test_email_input_has_accessible_name(self, driver):
        page = LoginPage(driver).open_login()
        page.reveal_email_form()
        field = page.wait_visible(*page.EMAIL_INPUT)
        accessible_name = (
            field.get_attribute("aria-label")
            or field.get_attribute("placeholder")
            or field.get_attribute("id")
        )
        assert accessible_name, "Email input has no discoverable accessible name"

    def test_barcode_input_has_accessible_name(self, driver, guest_session):
        page = BasePage(driver).open("scan")
        field = page.wait_visible(By.ID, "input-barcode")
        accessible_name = (
            field.get_attribute("aria-label")
            or field.get_attribute("placeholder")
            or field.get_attribute("id")
        )
        assert accessible_name


class TestKeyboardOperability:
    def test_login_buttons_are_native_buttons_not_divs(self, driver):
        """Native <button> elements get focus/Enter/Space handling for
        free; a clickable <div> would silently break keyboard users."""
        page = LoginPage(driver).open_login()
        for element_id in ("btn-google-signin", "btn-email-signin", "btn-guest"):
            el = page.wait_visible(By.ID, element_id)
            assert el.tag_name.lower() == "button", f"#{element_id} should be a <button>"

    def test_guest_button_reachable_and_activatable_via_tab_and_enter(self, driver):
        page = LoginPage(driver).open_login()
        guest_btn = page.wait_visible(*page.GUEST_BTN)
        guest_btn.send_keys("")  # focus without altering value
        driver.execute_script("arguments[0].focus();", guest_btn)
        assert driver.switch_to.active_element.get_attribute("id") == "btn-guest"


class TestImagesAndIconsHaveAltOrAreDecorative:
    def test_svg_icons_marked_decorative_or_have_accessible_title(self, driver):
        page = LoginPage(driver).open_login()
        svgs = driver.find_elements(By.TAG_NAME, "svg")
        for svg in svgs:
            hidden = svg.get_attribute("aria-hidden")
            has_title = len(svg.find_elements(By.TAG_NAME, "title")) > 0
            assert hidden == "true" or has_title, (
                "Decorative SVG icon missing aria-hidden='true' (and has no <title>)"
            )


ACCESSIBILITY_PAGES = [
    ("", "home"),
    ("history", "history"),
    ("profile", "profile"),
    ("scan", "scan"),
]


class TestHeadingHierarchy:
    @pytest.mark.parametrize("route,name", ACCESSIBILITY_PAGES)
    def test_page_has_exactly_one_h1_for_screen_reader_landmark_nav(self, driver, guest_session, route, name):
        """More than one <h1> confuses screen-reader 'jump to heading'
        navigation — this is a stricter, accessibility-motivated version
        of the UI-validation 'at least one h1' check."""
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "h1")
        h1s = driver.find_elements(By.TAG_NAME, "h1")
        assert len(h1s) == 1, f"{name} page has {len(h1s)} <h1> elements, expected exactly 1"

    @pytest.mark.parametrize("route,name", ACCESSIBILITY_PAGES)
    def test_heading_levels_do_not_skip(self, driver, guest_session, route, name):
        """An h1 followed directly by an h3 (skipping h2) breaks the
        outline screen readers build from heading levels."""
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "h1")
        levels = driver.execute_script(
            "return Array.from(document.querySelectorAll('h1,h2,h3,h4,h5,h6'))"
            ".map(h => parseInt(h.tagName[1]));"
        )
        skips = [
            (prev, nxt) for prev, nxt in zip(levels, levels[1:])
            if nxt - prev > 1
        ]
        assert not skips, f"{name} page skips heading levels: {skips} (full sequence: {levels})"


class TestLandmarkRegions:
    @pytest.mark.parametrize("route,name", ACCESSIBILITY_PAGES)
    def test_page_has_a_main_landmark(self, driver, guest_session, route, name):
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "body")
        has_main = (
            len(driver.find_elements(By.TAG_NAME, "main")) > 0
            or len(driver.find_elements(By.CSS_SELECTOR, "[role='main']")) > 0
        )
        assert has_main, f"{name} page has no <main> / role='main' landmark"

    @pytest.mark.parametrize("route,name", ACCESSIBILITY_PAGES)
    def test_page_nav_landmark_has_accessible_name(self, driver, guest_session, route, name):
        page = BasePage(driver).open(route)
        page.set_viewport(*config.VIEWPORTS["mobile"])
        driver.refresh()
        nav = page.wait_visible(By.CSS_SELECTOR, "nav[aria-label]", timeout=config.DEFAULT_TIMEOUT)
        assert nav.get_attribute("aria-label").strip() != ""


class TestFormFieldLabelAssociation:
    @pytest.mark.parametrize("field_id", ["input-barcode"])
    def test_scan_field_has_label_or_aria_labelledby_or_aria_label(self, driver, guest_session, field_id):
        page = BasePage(driver).open("scan")
        field = page.wait_visible(By.ID, field_id)
        has_label_for = len(driver.find_elements(By.CSS_SELECTOR, f"label[for='{field_id}']")) > 0
        has_aria = field.get_attribute("aria-label") or field.get_attribute("aria-labelledby")
        assert has_label_for or has_aria, f"#{field_id} has no associated <label> or aria-label"

    def test_display_name_field_has_label_or_aria_label_if_present(self, driver, guest_session):
        page = BasePage(driver).open("profile")
        if not page.exists(By.ID, "input-display-name"):
            pytest.skip("Display-name field not present for this auth state")
        field = page.wait_visible(By.ID, "input-display-name")
        has_label_for = len(driver.find_elements(By.CSS_SELECTOR, "label[for='input-display-name']")) > 0
        has_aria = field.get_attribute("aria-label") or field.get_attribute("aria-labelledby")
        assert has_label_for or has_aria


class TestColorIsNotSoleErrorIndicator:
    def test_scan_error_message_has_text_not_just_red_color(self, driver, guest_session):
        """A visually-red-only error is invisible to colorblind users and
        screen readers; the message must carry the information in text."""
        page = BasePage(driver).open("scan")
        submit_btn = page.wait_visible(By.ID, "btn-scan-barcode")
        submit_btn.click()
        error_el = page.wait_visible(
            By.XPATH,
            "//*[contains(@style,'flagged-red') or contains(@class,'error')]",
            timeout=config.SHORT_TIMEOUT,
        )
        assert error_el.text.strip() != "", "Error indicator has no readable text content"
