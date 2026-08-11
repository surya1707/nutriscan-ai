"""
Category: Navigation / Routing

NutriScan uses react-router's BrowserRouter (NOT HashRouter) with
basename="/nutriscan-ai/", deployed to GitHub Pages, which has no
server-side routing. That combination only works because of the
public/404.html client-side redirect script: GH Pages serves 404.html
for any unmatched deep link, and that script rewrites the URL back to
index.html with the real path preserved, which react-router then
restores. `vite preview` (used by this CI job) reproduces the same
history-fallback behaviour for local runs. These tests specifically
target THAT mechanism, not just "does routing work".
"""

import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from pages.login_page import LoginPage
from pages.base_page import BasePage
import config


pytestmark = pytest.mark.navigation


class TestDirectDeepLinkLoads:
    @pytest.mark.parametrize("route", ["login", "history", "profile", "scan"])
    def test_direct_load_of_deep_link_does_not_404(self, driver, route):
        """A hard browser navigation (not a client-side <Link> click)
        straight to a nested path must still resolve to the SPA, not a
        raw GitHub Pages / server 404 page."""
        page = BasePage(driver)
        page.open(route)
        WebDriverWait(driver, config.DEFAULT_TIMEOUT).until(
            lambda d: "nutriscan" in d.title.lower() or len(d.find_elements(
                By.TAG_NAME, "h1"
            )) > 0
        )
        assert "404" not in driver.title
        assert "nutriscan" in driver.title.lower() or driver.find_elements(
            By.TAG_NAME, "h1"
        )

    def test_direct_load_of_protected_deep_link_still_enforces_auth(self, driver):
        """The redirect mechanism must not accidentally bypass
        ProtectedRoute — landing hard on /history unauthenticated still
        has to bounce to /login."""
        page = BasePage(driver)
        page.clear_local_storage()
        page.open("history")
        page.wait_for_path("/login", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/login"


class TestReloadOnDeepLink:
    def test_reload_while_on_a_nested_authenticated_route_stays_put(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)

        page = BasePage(driver).open("profile")
        page.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)

        driver.refresh()
        page.wait_for_path("/profile", timeout=config.DEFAULT_TIMEOUT)
        assert page.current_path().rstrip("/") == "/profile"


class TestTrailingSlashesAndCasing:
    @pytest.mark.parametrize("route", ["history/", "HISTORY", "History"])
    def test_route_variants_resolve_without_crashing(self, driver, route):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "body")
        # Either it resolves to /history (case/slash-insensitive routing)
        # or falls back to the catch-all -> '/'; it must never show a raw
        # dead page with no app chrome.
        assert page.exists(By.ID, "btn-user-avatar") or \
               page.current_path().rstrip("/") in ("", "/history")


class TestQueryStringHandling:
    @pytest.mark.parametrize("route", ["history?sort=recent", "profile?tab=settings", "?ref=email"])
    def test_query_string_does_not_break_route_resolution(self, driver, route):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "body")
        assert page.exists(By.ID, "btn-user-avatar")

    def test_query_string_preserved_in_address_bar_after_load(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open("history?sort=recent")
        page.wait_present(By.TAG_NAME, "body")
        assert "sort=recent" in driver.current_url

    def test_unknown_query_params_do_not_crash_protected_pages(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open("scan?utm_source=test&foo=<script>bar")
        page.wait_present(By.TAG_NAME, "body")
        assert driver.find_element(By.TAG_NAME, "body").text.strip() != ""


class TestHashFragmentHandling:
    def test_hash_fragment_does_not_break_browserrouter_navigation(self, driver):
        """This app uses BrowserRouter (not HashRouter) — a stray '#'
        fragment must be treated as an in-page anchor, never as part of
        the route path itself."""
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open("history#section-2")
        page.wait_present(By.TAG_NAME, "body")
        assert "/history" in page.current_path() or page.current_path().rstrip("/") in ("", "/")

    def test_bare_hash_on_root_does_not_crash(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open("#top")
        page.wait_present(By.TAG_NAME, "body")
        assert driver.find_element(By.TAG_NAME, "body").text.strip() != ""


class TestEncodedPathSegments:
    @pytest.mark.parametrize("route", ["results/%20", "results/new%00", "history%2F"])
    def test_url_encoded_path_segments_do_not_crash_the_app(self, driver, route):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open(route)
        page.wait_present(By.TAG_NAME, "body")
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text


class TestMultipleConsecutiveSlashes:
    def test_double_slash_in_path_resolves_gracefully(self, driver):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open("history//")
        page.wait_present(By.TAG_NAME, "body")
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text


class TestResultsRouteIdVariants:
    @pytest.mark.parametrize("scan_id", [
        "new", "123", "abc-def-123", "00000000-0000-0000-0000-000000000000",
        "<script>alert(1)</script>", "../../etc/passwd", "%2e%2e%2f",
    ])
    def test_results_route_accepts_arbitrary_id_segments_without_crashing(self, driver, scan_id):
        login = LoginPage(driver).open_login()
        login.continue_as_guest()
        login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
        page = BasePage(driver).open(f"results/{scan_id}")
        page.wait_present(By.TAG_NAME, "body")
        body_text = driver.find_element(By.TAG_NAME, "body").text.lower()
        assert "uncaught" not in body_text
