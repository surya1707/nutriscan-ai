from selenium.webdriver.common.by import By

from pages.base_page import BasePage


class AppShell(BasePage):
    """
    Wraps the persistent chrome around every protected page: top bar,
    sidebar/bottom-bar/drawer navigation, and the user avatar menu.

    AppShell renders desktop sidebar nav, mobile bottom-tab nav, and a
    tablet drawer nav all in the DOM simultaneously (see base_page.py
    docstring) — every method below resolves to whichever instance is
    actually visible at the current viewport.
    """

    NAV_LINK = "nav a[href*='{path}']"
    AVATAR_BTN = (By.ID, "btn-user-avatar")
    SIGNOUT_BTN = (By.ID, "btn-signout")
    HAMBURGER_BTN = (By.ID, "btn-hamburger")
    BOTTOM_NAV = (By.CSS_SELECTOR, "nav.bottom-nav, nav[aria-label='Main navigation']")
    DRAWER_OVERLAY_SIGNAL = (By.XPATH, "//div[contains(@style,'rgba(0,0,0,0.3)')]")

    def nav_to(self, path: str):
        """path e.g. '', 'history', 'profile'. Uses whichever nav instance is visible."""
        selector = self.NAV_LINK.format(path=path if path else "\"/\"")
        # NavLink hrefs are exact paths ('/', '/history', '/profile'); for
        # home ('/') a substring match on href*='/' would match everything,
        # so special-case it via the visible-text fallback instead.
        if path == "":
            self.click_visible(By.XPATH, "//nav//a[.//span[text()='Home'] or text()='Home']")
        else:
            self.click_visible(By.CSS_SELECTOR, f"nav a[href*='/{path}']")
        return self

    def open_hamburger_drawer(self):
        self.click_visible(*self.HAMBURGER_BTN)
        return self

    def is_drawer_open(self) -> bool:
        return len(self.find_all_visible(*self.DRAWER_OVERLAY_SIGNAL)) > 0

    def open_avatar_menu(self):
        self.click_visible(*self.AVATAR_BTN)
        return self

    def sign_out(self):
        self.open_avatar_menu()
        self.click_visible(*self.SIGNOUT_BTN)
        return self

    def visible_nav_link_count(self, path: str) -> int:
        """How many *visible* nav links point at `path` right now (should be exactly 1)."""
        if path == "":
            els = self.find_all_visible(By.XPATH, "//nav//a[.//span[text()='Home'] or text()='Home']")
        else:
            els = self.find_all_visible(By.CSS_SELECTOR, f"nav a[href*='/{path}']")
        return len(els)

    def active_layout(self) -> str:
        """Best-effort classification of which chrome variant is currently visible."""
        sidebar_visible = len(self.find_all_visible(By.CSS_SELECTOR, "aside.sidebar-desktop")) > 0
        bottom_visible = len(self.find_all_visible(By.CSS_SELECTOR, "nav.bottom-nav")) > 0
        if sidebar_visible:
            return "desktop"
        if bottom_visible:
            return "mobile"
        return "tablet"
