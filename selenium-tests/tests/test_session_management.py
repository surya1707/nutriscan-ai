"""Category: Session Management"""

import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.base_page import BasePage
from pages.app_shell import AppShell
import config


pytestmark = pytest.mark.session


class TestGuestSessionPersistence:
    def test_guest_session_survives_page_reload(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        driver.refresh()
        page = BasePage(driver)
        # A reload must NOT bounce a guest back to /login.
        page.wait_present(By.TAG_NAME, "body")
        assert "login" not in page.current_path()

    def test_guest_session_survives_navigating_to_a_new_url_bar_entry(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open("profile")
        page.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/profile"

    def test_manually_injecting_guest_flag_before_load_bypasses_login(self, driver):
        """Two-tier-login-style check: setting the exact localStorage key
        the app reads (see authStore.ts GUEST_KEY) before first load must
        produce the same authenticated state as clicking the button."""
        base = BasePage(driver)
        base.open(config.ROUTES["login"])
        base.set_local_storage(config.GUEST_KEY, "true")
        base.driver.refresh()
        base.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        assert base.current_path().rstrip("/") in ("", "/")


class TestLogoutClearsSession:
    def test_logout_then_direct_protected_url_redirects_to_login(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)

        shell = AppShell(driver)
        shell.sign_out()
        shell.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)

        page = BasePage(driver).open("history")
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"

    def test_logout_clears_guest_local_storage_key(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)

        shell = AppShell(driver)
        shell.sign_out()
        shell.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert shell.get_local_storage(config.GUEST_KEY) in (None, "false")


class TestFreshSessionHasNoStaleState:
    def test_clean_browser_profile_starts_unauthenticated(self, driver):
        page = BasePage(driver)
        page.open("")
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"


class TestSessionPersistenceAcrossMultiStepNavigation:
    def test_guest_session_survives_a_three_page_navigation_chain(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)

        shell = AppShell(driver)
        for target, expected in [("history", "/history"), ("profile", "/profile"), ("", "/")]:
            shell.nav_to(target)
            shell.wait_for_path(expected, timeout=config.DEFAULT_TIMEOUT)
            assert "login" not in shell.current_path()

    def test_guest_session_survives_reload_on_every_protected_route(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)

        for route in ["history", "profile", "scan", "results/new"]:
            page = BasePage(driver).open(route)
            page.wait_present(By.TAG_NAME, "body")
            driver.refresh()
            page.wait_present(By.TAG_NAME, "body")
            assert "login" not in page.current_path(), f"Reload on '{route}' lost the guest session"


class TestUnrelatedLocalStorageDoesNotAffectSession:
    def test_unrelated_keys_do_not_interfere_with_guest_auth(self, driver):
        login = LoginPage(driver).open_login()
        login.set_local_storage("some-other-app-key", "irrelevant-value")
        login.set_local_storage("theme-preference", "dark")
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        assert login.get_local_storage(config.GUEST_KEY) == "true"

    def test_clearing_an_unrelated_key_does_not_log_out_a_guest(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        login.set_local_storage("unrelated-key", "value")
        login.driver.execute_script(
            "window.localStorage.removeItem('unrelated-key');"
        )
        driver.refresh()
        page = BasePage(driver)
        page.wait_present(By.TAG_NAME, "body")
        assert "login" not in page.current_path()


class TestEmailForSignInKeyIsolation:
    """authStore.ts also persists EMAIL_LINK_KEY for the magic-link flow —
    verify it doesn't accidentally grant guest-equivalent access."""

    def test_email_link_key_alone_does_not_grant_access(self, driver):
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.set_local_storage(config.EMAIL_LINK_KEY, "someone@example.com")
        page.open("history")
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"

    def test_email_link_key_survives_alongside_guest_flag(self, driver):
        """A user who started the email flow and then chose Guest instead
        shouldn't have any leftover state break the guest session."""
        page = BasePage(driver)
        page.clear_local_storage()
        page.open(config.ROUTES["login"])
        page.set_local_storage(config.EMAIL_LINK_KEY, "someone@example.com")
        page.set_local_storage(config.GUEST_KEY, "true")
        page.open("")
        page.wait_present(By.TAG_NAME, "body")
        assert "login" not in page.current_path()


class TestMultipleSignOutCallsAreSafe:
    def test_signing_out_twice_in_a_row_does_not_error(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        shell = AppShell(driver)
        shell.sign_out()
        shell.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        # Re-authenticate and sign out again — must behave identically,
        # not throw due to leftover state from the first sign-out.
        login2 = LoginPage(driver)
        login2.continue_as_guest()
        login2.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        shell.sign_out()
        shell.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert shell.current_path().rstrip("/") == "/login"
