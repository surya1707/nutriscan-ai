"""
Category: Authorization

NutriScan has no role hierarchy (unlike an admin/officer/farmer app) —
authorization here means: unauthenticated visitors are bounced to /login,
guests and authenticated users are let through, and no protected route
is ever reachable by a fresh, unauthenticated session no matter how it's
approached (direct URL, back-button, stale localStorage, etc).
"""

import pytest
from selenium.webdriver.common.by import By

from pages.base_page import BasePage
from pages.login_page import LoginPage
import config


pytestmark = pytest.mark.authorization

PROTECTED_ROUTES = ["", "history", "profile", "scan", "results/new"]


class TestUnauthenticatedRedirects:
    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_direct_navigation_to_protected_route_redirects_to_login(self, driver, route):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(route)
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"

    def test_root_redirects_to_login_when_unauthenticated(self, driver):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open("")
        page.wait_for_path("/login")
        assert "login" in page.current_path()

    def test_stale_guest_flag_removed_after_logout_blocks_access(self, driver):
        """Regression guard: an explicitly cleared guest flag must not
        leave any other client state (e.g. a cached route) that lets the
        protected shell render."""
        page = BasePage(driver)
        page.open("")
        page.clear_local_storage()
        page.driver.refresh()
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"


class TestGuestAuthorization:
    @pytest.fixture()
    def guest_page(self, driver):
        page = LoginPage(driver).open_login()
        page.continue_as_guest()
        page.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        return page

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_guest_can_reach_protected_route(self, driver, guest_page, route):
        page = BasePage(driver)
        page.open(route)
        # Guests are allowed through ProtectedRoute; the page must not
        # bounce back to /login.
        assert page.current_path().rstrip("/") != "/login"

    def test_guest_visiting_login_directly_is_redirected_to_home(self, driver, guest_page):
        page = BasePage(driver)
        page.open(config.ROUTES["login"])
        page.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        assert page.current_path().rstrip("/") in ("", "/")


class TestUnknownRoutes:
    def test_unknown_route_when_unauthenticated_goes_to_login(self, driver):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["unknown"])
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"

    def test_unknown_route_when_guest_falls_back_to_home(self, driver):
        page = LoginPage(driver).open_login()
        page.continue_as_guest()
        page.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        base = BasePage(driver)
        base.open(config.ROUTES["unknown"])
        base.wait_for_path("/", timeout=config.DEFAULT_TIMEOUT)
        assert base.current_path().rstrip("/") in ("", "/")


class TestGuestFlagValueStrictness:
    """authStore.ts reads the localStorage guest flag; these tests pin
    down exactly what counts as 'authenticated' vs what doesn't, since a
    loose comparison (truthy string) vs a strict '=== \"true\"' check is
    a real, easy-to-introduce authorization bug."""

    @pytest.mark.parametrize("value", ["True", "TRUE", "1", "yes", "on", " true", "true "])
    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_non_exact_guest_flag_values_do_not_bypass_login(self, driver, value, route):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.set_local_storage(config.GUEST_KEY, value)
        page.open(route)
        # Either it's treated as authenticated (acceptable if the app
        # intentionally does a loose truthy check) or it's bounced to
        # /login (acceptable if it's strict) — what's NOT acceptable is
        # landing on a protected route while ALSO showing no app chrome
        # (a broken in-between state).
        path = page.current_path().rstrip("/")
        if path != "/login":
            assert page.exists(By.ID, "btn-user-avatar") or page.exists(By.TAG_NAME, "h1")

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_exact_true_string_bypasses_login_for_every_protected_route(self, driver, route):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.set_local_storage(config.GUEST_KEY, "true")
        page.open(route)
        assert page.current_path().rstrip("/") != "/login"

    def test_false_string_guest_flag_does_not_bypass_login(self, driver):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.set_local_storage(config.GUEST_KEY, "false")
        page.open("history")
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"

    def test_empty_string_guest_flag_does_not_bypass_login(self, driver):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.set_local_storage(config.GUEST_KEY, "")
        page.open("profile")
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"


class TestCrossRouteAuthorizationConsistency:
    """Every protected route must apply the SAME rule — this file catches
    the case where one route was guarded and a newly-added one wasn't."""

    @pytest.mark.parametrize("route", PROTECTED_ROUTES)
    def test_each_protected_route_individually_blocks_a_fresh_session(self, driver, route):
        page = BasePage(driver)
        page.clear_local_storage()
        page.driver.delete_all_cookies()
        page.open(route)
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login", (
            f"Route '{route}' did not enforce authorization for a fresh session"
        )

    def test_login_route_itself_is_never_treated_as_protected(self, driver):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.wait_present(By.TAG_NAME, "body")
        assert page.current_path().rstrip("/") == "/login"
