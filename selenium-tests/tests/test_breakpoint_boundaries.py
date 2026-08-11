"""
Category: Responsive — breakpoint boundaries

test_responsive.py checks three representative viewport sizes; this file
checks the exact pixel values AppShell.tsx's inline <style> switches at
(< 768px, 768-1023px, >= 1024px) — the off-by-one values most likely to
actually break (767 vs 768, 1023 vs 1024) rather than a size safely in
the middle of a range.
"""

import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.app_shell import AppShell
import config


pytestmark = pytest.mark.responsive

HEIGHT = 900  # height doesn't affect these breakpoints; keep it constant

BOUNDARY_WIDTHS = [
    (767, "mobile"),   # just below the tablet breakpoint
    (768, "tablet"),   # exact tablet breakpoint
    (769, "tablet"),   # just above it
    (1023, "tablet"),  # just below the desktop breakpoint
    (1024, "desktop"), # exact desktop breakpoint
    (1025, "desktop"), # just above it
]


@pytest.fixture()
def guest_shell(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return AppShell(driver)


class TestExactBreakpointWidths:
    @pytest.mark.parametrize("width,expected_layout", BOUNDARY_WIDTHS)
    def test_layout_at_exact_breakpoint_width(self, driver, guest_shell, width, expected_layout):
        guest_shell.set_viewport(width, HEIGHT)
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        assert guest_shell.active_layout() == expected_layout, (
            f"At {width}px expected '{expected_layout}' layout, "
            f"got '{guest_shell.active_layout()}'"
        )

    @pytest.mark.parametrize("width,expected_layout", BOUNDARY_WIDTHS)
    def test_exactly_one_visible_nav_link_at_boundary_width(self, driver, guest_shell, width, expected_layout):
        guest_shell.set_viewport(width, HEIGHT)
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        if expected_layout == "tablet":
            guest_shell.open_hamburger_drawer()
        assert guest_shell.visible_nav_link_count("history") == 1, (
            f"At {width}px ({expected_layout}) expected exactly one visible "
            f"'history' nav link, got {guest_shell.visible_nav_link_count('history')}"
        )

    @pytest.mark.parametrize("width,expected_layout", BOUNDARY_WIDTHS)
    def test_navigation_reachable_at_boundary_width(self, driver, guest_shell, width, expected_layout):
        guest_shell.set_viewport(width, HEIGHT)
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        if expected_layout == "tablet":
            guest_shell.open_hamburger_drawer()
        guest_shell.nav_to("profile")
        guest_shell.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)
        assert guest_shell.current_path().rstrip("/") == "/profile"


class TestNoLayoutBreakageAtBoundaries:
    @pytest.mark.parametrize("width,expected_layout", BOUNDARY_WIDTHS)
    def test_no_horizontal_overflow_at_boundary_width(self, driver, guest_shell, width, expected_layout):
        guest_shell.set_viewport(width, HEIGHT)
        guest_shell.driver.refresh()
        guest_shell.wait_present(By.TAG_NAME, "body")
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        assert scroll_width <= client_width + 2, (
            f"Horizontal overflow at exactly {width}px ({scroll_width}px content "
            f"in {client_width}px viewport)"
        )

    @pytest.mark.parametrize("width,expected_layout", BOUNDARY_WIDTHS)
    def test_avatar_button_stays_visible_at_boundary_width(self, driver, guest_shell, width, expected_layout):
        """The avatar/account entry point must never disappear entirely —
        regardless of which chrome variant is active."""
        guest_shell.set_viewport(width, HEIGHT)
        guest_shell.driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        assert guest_shell.find_all_visible(*guest_shell.AVATAR_BTN)
