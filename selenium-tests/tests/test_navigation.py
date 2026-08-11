"""Category: Navigation"""

import pytest

from pages.login_page import LoginPage
from pages.app_shell import AppShell
from pages.base_page import BasePage
import config


pytestmark = pytest.mark.navigation


@pytest.fixture()
def guest_session(driver):
    page = LoginPage(driver).open_login()
    page.continue_as_guest()
    page.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    return driver


class TestNavBarLinks:
    @pytest.mark.parametrize("target,expected_path", [
        ("history", "/history"),
        ("profile", "/profile"),
        ("", "/"),
    ])
    def test_nav_link_navigates_to_expected_route(self, driver, guest_session, target, expected_path):
        shell = AppShell(driver)
        shell.nav_to(target)
        shell.wait_for_path(expected_path, timeout=config.DEFAULT_TIMEOUT)
        assert shell.current_path().rstrip("/") == expected_path.rstrip("/") or (
            expected_path == "/" and shell.current_path().rstrip("/") == ""
        )

    def test_exactly_one_visible_nav_instance_per_link_desktop(self, driver, guest_session):
        shell = AppShell(driver).set_viewport(*config.VIEWPORTS["desktop"])
        driver.refresh()
        shell.wait_present(*shell.AVATAR_BTN)
        for path in ("history", "profile"):
            assert shell.visible_nav_link_count(path) == 1, (
                f"Expected exactly 1 visible '{path}' nav link on desktop, "
                f"got {shell.visible_nav_link_count(path)} (dual-nav DOM bug)"
            )

    def test_exactly_one_visible_nav_instance_per_link_mobile(self, driver, guest_session):
        shell = AppShell(driver).set_viewport(*config.VIEWPORTS["mobile"])
        driver.refresh()
        shell.wait_present(*shell.AVATAR_BTN)
        for path in ("history", "profile"):
            assert shell.visible_nav_link_count(path) == 1, (
                f"Expected exactly 1 visible '{path}' nav link on mobile, "
                f"got {shell.visible_nav_link_count(path)} (dual-nav DOM bug)"
            )


class TestBrowserBackForward:
    def test_back_button_returns_to_previous_page(self, driver, guest_session):
        shell = AppShell(driver)
        shell.nav_to("history")
        shell.wait_for_path("/history")
        driver.back()
        shell.wait_for_path("/")
        assert shell.current_path().rstrip("/") in ("", "/")

    def test_forward_button_replays_navigation(self, driver, guest_session):
        shell = AppShell(driver)
        shell.nav_to("history")
        shell.wait_for_path("/history")
        driver.back()
        shell.wait_for_path("/")
        driver.forward()
        shell.wait_for_path("/history")
        assert shell.current_path().rstrip("/") == "/history"


class TestAvatarMenuAndLogout:
    def test_avatar_menu_opens(self, driver, guest_session):
        shell = AppShell(driver)
        shell.open_avatar_menu()
        assert shell.exists(*shell.SIGNOUT_BTN)

    def test_sign_out_redirects_to_login(self, driver, guest_session):
        shell = AppShell(driver)
        shell.sign_out()
        shell.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert shell.current_path().rstrip("/") == "/login"

    def test_sign_out_clears_guest_flag(self, driver, guest_session):
        shell = AppShell(driver)
        shell.sign_out()
        shell.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert shell.get_local_storage(config.GUEST_KEY) in (None, "false")


class TestTabletDrawerNavigation:
    def test_hamburger_opens_drawer_on_tablet(self, driver, guest_session):
        shell = AppShell(driver).set_viewport(*config.VIEWPORTS["tablet"])
        driver.refresh()
        shell.wait_present(*shell.AVATAR_BTN)
        shell.open_hamburger_drawer()
        assert shell.is_drawer_open()

    def test_drawer_link_navigates_and_closes_drawer(self, driver, guest_session):
        shell = AppShell(driver).set_viewport(*config.VIEWPORTS["tablet"])
        driver.refresh()
        shell.wait_present(*shell.AVATAR_BTN)
        shell.open_hamburger_drawer()
        shell.nav_to("profile")
        shell.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)
        assert not shell.is_drawer_open()


class TestFullRouteToRouteMatrix:
    """Every ordered pair of (home, history, profile) reached purely via
    the nav bar, on desktop. Catches a single broken link that a
    happy-path 'click each link once from home' test would miss."""

    ROUTE_PAIRS = [
        ("", "history", "/history"),
        ("", "profile", "/profile"),
        ("history", "profile", "/profile"),
        ("history", "", "/"),
        ("profile", "history", "/history"),
        ("profile", "", "/"),
    ]

    @pytest.mark.parametrize("start,target,expected_path", ROUTE_PAIRS)
    def test_navigate_from_route_to_route(self, driver, guest_session, start, target, expected_path):
        shell = AppShell(driver).set_viewport(*config.VIEWPORTS["desktop"])
        BasePage(driver).open(start)
        shell.wait_present(*shell.AVATAR_BTN)
        shell.nav_to(target)
        shell.wait_for_path(expected_path, timeout=config.DEFAULT_TIMEOUT)
        got = shell.current_path().rstrip("/")
        assert got == expected_path.rstrip("/") or (expected_path == "/" and got == "")


class TestMultiStepBackForwardChains:
    def test_three_step_back_chain_replays_in_reverse_order(self, driver, guest_session):
        shell = AppShell(driver)
        shell.nav_to("history")
        shell.wait_for_path("/history")
        shell.nav_to("profile")
        shell.wait_for_path("/profile")
        BasePage(driver).open("scan")
        shell.wait_for_path("/scan")

        driver.back()
        shell.wait_for_path("/profile")
        driver.back()
        shell.wait_for_path("/history")
        driver.back()
        shell.wait_for_path("/")
        assert shell.current_path().rstrip("/") in ("", "/")

    def test_three_step_forward_chain_replays_original_order(self, driver, guest_session):
        shell = AppShell(driver)
        shell.nav_to("history")
        shell.wait_for_path("/history")
        shell.nav_to("profile")
        shell.wait_for_path("/profile")

        driver.back()
        shell.wait_for_path("/history")
        driver.back()
        shell.wait_for_path("/")

        driver.forward()
        shell.wait_for_path("/history")
        driver.forward()
        shell.wait_for_path("/profile")
        assert shell.current_path().rstrip("/") == "/profile"

    def test_navigating_after_going_back_truncates_forward_history(self, driver, guest_session):
        shell = AppShell(driver)
        shell.nav_to("history")
        shell.wait_for_path("/history")
        driver.back()
        shell.wait_for_path("/")
        shell.nav_to("profile")
        shell.wait_for_path("/profile")
        driver.forward()
        # Forward history was truncated by the new navigation; the URL
        # bar should still show /profile (nothing to go forward to).
        assert shell.current_path().rstrip("/") == "/profile"


class TestNavFromEveryPage:
    """Scan and Results also carry the persistent AppShell nav — verify
    it works from there too, not just from Home/History/Profile."""

    def test_nav_works_from_scan_page(self, driver, guest_session):
        shell = AppShell(driver)
        BasePage(driver).open("scan")
        shell.wait_present(*shell.AVATAR_BTN)
        shell.nav_to("history")
        shell.wait_for_path("/history", timeout=config.DEFAULT_TIMEOUT)
        assert shell.current_path().rstrip("/") == "/history"

    def test_nav_works_from_results_page(self, driver, guest_session):
        shell = AppShell(driver)
        BasePage(driver).open("results/new")
        shell.wait_present(*shell.AVATAR_BTN)
        shell.nav_to("")
        shell.wait_for_path("/", timeout=config.DEFAULT_TIMEOUT)
        assert shell.current_path().rstrip("/") in ("", "/")
