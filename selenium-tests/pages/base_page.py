"""
Base page object.

Key gotcha this file exists to solve: AppShell renders THREE navigation
instances in the DOM at once (desktop sidebar, mobile bottom bar, tablet
drawer) and switches which one is visible purely via CSS media queries.
A plain `find_element(By.LINK_TEXT, "History")` will happily return a
*hidden* one and Selenium will raise ElementNotInteractableException.
Every "find a nav-ish thing" helper here filters to elements that are
actually displayed at the current viewport before returning.
"""

import os
import time

from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import config


class BasePage:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, config.DEFAULT_TIMEOUT)
        self.short_wait = WebDriverWait(driver, config.SHORT_TIMEOUT)

    # ── Navigation ───────────────────────────────────────────────────
    def open(self, route: str = ""):
        url = config.BASE_URL + route
        self.driver.get(url)
        return self

    def current_path(self) -> str:
        """Path relative to the app basename, e.g. '/scan'. Empty string == home."""
        url = self.driver.current_url
        marker = "/nutriscan-ai/"
        idx = url.find(marker)
        if idx == -1:
            return url
        rest = url[idx + len(marker):]
        rest = rest.split("?")[0].split("#")[0]
        return "/" + rest if rest and not rest.startswith("/") else (rest or "/")

    def wait_for_path(self, expected: str, timeout: int = None):
        t = timeout or config.DEFAULT_TIMEOUT

        def _check(_driver):
            path = self.current_path().rstrip("/") or "/"
            expected_norm = ("/" + expected.strip("/")) if expected not in ("", "/") else "/"
            return path == expected_norm

        WebDriverWait(self.driver, t).until(_check, message=(
            f"Expected path '{expected}', got '{self.current_path()}' "
            f"(url={self.driver.current_url})"
        ))
        return self

    # ── Visible-element helpers (the fix for the triple-nav problem) ──
    def find_visible(self, by, selector, timeout: int = None):
        t = timeout or config.DEFAULT_TIMEOUT

        def _first_visible(drv):
            els = drv.find_elements(by, selector)
            for el in els:
                try:
                    if el.is_displayed():
                        return el
                except StaleElementReferenceException:
                    continue
            return False

        return WebDriverWait(self.driver, t).until(
            _first_visible,
            message=f"No visible element matched ({by}, {selector!r})",
        )

    def find_all_visible(self, by, selector):
        els = self.driver.find_elements(by, selector)
        return [el for el in els if self._safe_displayed(el)]

    @staticmethod
    def _safe_displayed(el) -> bool:
        try:
            return el.is_displayed()
        except StaleElementReferenceException:
            return False

    def click_visible(self, by, selector, timeout: int = None):
        el = self.find_visible(by, selector, timeout)
        self.wait_clickable(el, timeout)
        el.click()
        return self

    def wait_clickable(self, el, timeout: int = None):
        t = timeout or config.DEFAULT_TIMEOUT
        WebDriverWait(self.driver, t).until(lambda _d: el.is_enabled() and el.is_displayed())
        return el

    # ── Generic waits ───────────────────────────────────────────────
    def wait_present(self, by, selector, timeout: int = None):
        t = timeout or config.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(EC.presence_of_element_located((by, selector)))

    def wait_visible(self, by, selector, timeout: int = None):
        t = timeout or config.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(EC.visibility_of_element_located((by, selector)))

    def wait_gone(self, by, selector, timeout: int = None):
        t = timeout or config.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, t).until(EC.invisibility_of_element_located((by, selector)))

    def exists(self, by, selector) -> bool:
        return len(self.driver.find_elements(by, selector)) > 0

    def text_present(self, text: str, timeout: int = None) -> bool:
        t = timeout or config.SHORT_TIMEOUT
        try:
            WebDriverWait(self.driver, t).until(
                lambda d: text.lower() in d.find_element(By.TAG_NAME, "body").text.lower()
            )
            return True
        except TimeoutException:
            return False

    # ── localStorage helpers (guest-mode login, session persistence) ──
    def set_local_storage(self, key: str, value: str):
        self.driver.execute_script(
            "window.localStorage.setItem(arguments[0], arguments[1]);", key, value
        )

    def get_local_storage(self, key: str):
        return self.driver.execute_script(
            "return window.localStorage.getItem(arguments[0]);", key
        )

    def clear_local_storage(self):
        if self.driver.current_url.startswith("data:") or self.driver.current_url == "about:blank":
            self.open("")
        self.driver.execute_script("window.localStorage.clear();")

    # ── Viewport ────────────────────────────────────────────────────
    def set_viewport(self, width: int, height: int):
        self.driver.set_window_size(width, height)
        return self
