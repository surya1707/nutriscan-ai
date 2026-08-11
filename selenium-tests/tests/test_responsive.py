"""
Category: Responsive

Uses the app's OWN breakpoints (see AppShell.tsx inline <style>: <768px
bottom nav, 768-1023px hamburger+drawer, >=1024px fixed sidebar) rather
than arbitrary device names, so a failure here means the app's actual
CSS contract broke, not that a guessed viewport doesn't match reality.
"""

import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.app_shell import AppShell
import config


pytestmark = pytest.mark.responsive


@pytest.fixture()
def guest_shell(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return AppShell(driver)


class TestLayoutSwitchesAtBreakpoints:
    def test_mobile_viewport_shows_bottom_nav_not_sidebar(self, driver, guest_shell):
        guest_shell.set_viewport(*config.VIEWPORTS["mobile"])
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        assert guest_shell.active_layout() == "mobile"
        assert not guest_shell.find_all_visible(By.CSS_SELECTOR, "aside.sidebar-desktop")

    def test_tablet_viewport_shows_hamburger_not_bottom_nav(self, driver, guest_shell):
        guest_shell.set_viewport(*config.VIEWPORTS["tablet"])
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        assert guest_shell.active_layout() == "tablet"
        assert not guest_shell.find_all_visible(By.CSS_SELECTOR, "nav.bottom-nav")

    def test_desktop_viewport_shows_sidebar_not_bottom_nav(self, driver, guest_shell):
        guest_shell.set_viewport(*config.VIEWPORTS["desktop"])
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)
        assert guest_shell.active_layout() == "desktop"
        assert not guest_shell.find_all_visible(By.CSS_SELECTOR, "nav.bottom-nav")


class TestNavigationWorksAtEveryBreakpoint:
    @pytest.mark.parametrize("viewport_name", ["mobile", "tablet", "desktop"])
    def test_can_reach_history_from_every_breakpoint(self, driver, guest_shell, viewport_name):
        guest_shell.set_viewport(*config.VIEWPORTS[viewport_name])
        driver.refresh()
        guest_shell.wait_present(*guest_shell.AVATAR_BTN)

        if viewport_name == "tablet":
            guest_shell.open_hamburger_drawer()

        guest_shell.nav_to("history")
        guest_shell.wait_for_path("/history", timeout=config.DEFAULT_TIMEOUT)
        assert guest_shell.current_path().rstrip("/") == "/history"


class TestNoHorizontalOverflow:
    @pytest.mark.parametrize("viewport_name", ["mobile", "tablet", "desktop"])
    @pytest.mark.parametrize("route", ["", "history", "profile", "scan"])
    def test_no_horizontal_scrollbar_introduced(self, driver, guest_shell, viewport_name, route):
        width, height = config.VIEWPORTS[viewport_name]
        guest_shell.set_viewport(width, height)
        guest_shell.open(route)
        guest_shell.wait_present(By.TAG_NAME, "body")
        scroll_width = driver.execute_script("return document.documentElement.scrollWidth;")
        client_width = driver.execute_script("return document.documentElement.clientWidth;")
        # Small tolerance for scrollbar gutter rounding.
        assert scroll_width <= client_width + 2, (
            f"{route or 'home'} page overflows horizontally at {viewport_name} "
            f"({scroll_width}px content in {client_width}px viewport)"
        )
