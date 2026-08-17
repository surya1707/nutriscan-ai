"""
Base page object.

Key rules baked in (see mobile-tests/README.md "gotchas" for the evidence):
  - `.text` only resolves for Text/EditableText widgets. Every other
    widget (IconButton, GestureDetector, Container, ...) must be checked
    with is_displayed(), never `.text`.
  - appium-flutter-driver has no page_source and no URL/route concept.
    "Which screen am I on" is answered via a visible-text marker map
    (config.ROUTE_TEXT_MARKERS), not a route inspection API.
  - Finders are by ValueKey wherever the widget tree has one (added
    alongside this suite — see mobile/lib key: const ValueKey(...) sites).
    Falling back to by_text is only safe for screens with no ambiguous
    duplicate-label widgets; this app's BottomNavigationBar is classic
    Material 2 (single label per tab, not the Material 3 dual-label
    crossfade), so by_text fallback on nav labels is fine here — this is
    a real, confirmed difference from the KrishiIQ reference app, not an
    assumption.
"""

import signal
import time

from appium_flutter_finder.flutter_finder import FlutterFinder
from selenium.common.exceptions import TimeoutException

import config
from utils import adb_helpers

finder = FlutterFinder()


class BasePage:
    def __init__(self, driver):
        self.driver = driver

    # ── Finding ──────────────────────────────────────────────────────
    def by_key(self, key: str):
        return finder.by_value_key(key)

    def by_text(self, text: str):
        return finder.by_text(text)

    def by_tooltip(self, tooltip: str):
        return finder.by_tooltip(tooltip)

    # ── Waiting ──────────────────────────────────────────────────────
    def wait_for_key(self, key: str, timeout: int = None) -> bool:
        timeout = timeout or config.DEFAULT_TIMEOUT
        el_finder = self.by_key(key)
        deadline = time.time() + timeout
        last_err = None
        while time.time() < deadline:
            try:
                # existence check only — never .text on a generic widget
                self.driver.execute_script("flutter:waitFor", el_finder, 1000)
                return True
            except Exception as e:  # noqa: BLE001 - polling loop, retry until deadline
                last_err = e
                time.sleep(0.3)
        raise TimeoutException(
            f"ValueKey '{key}' not found within {timeout}s (last error: {last_err})"
        )

    def is_displayed_by_key(self, key: str) -> bool:
        try:
            self.wait_for_key(key, timeout=config.SHORT_TIMEOUT)
            return True
        except TimeoutException:
            return False

    def wait_for_text(self, text: str, timeout: int = None) -> bool:
        timeout = timeout or config.DEFAULT_TIMEOUT
        el_finder = self.by_text(text)
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                self.driver.execute_script("flutter:waitFor", el_finder, 1000)
                return True
            except Exception:  # noqa: BLE001
                time.sleep(0.3)
        return False

    # ── Actions ──────────────────────────────────────────────────────
    def tap_key(self, key: str, timeout: int = None) -> None:
        self.wait_for_key(key, timeout)
        # appium-flutter-driver@2.19.0 registers this handler as
        # "clickElement", not "click" — "flutter:click" throws
        # `Command not supported: "flutter:click"` immediately (verified
        # against execute.js's commandHandlers table). This was the root
        # cause of the near-100% Android E2E failure rate: almost every
        # test taps something as its first real action, so the whole
        # suite failed at step one and burned the rest of its budget on
        # doomed rerun/timeout loops.
        self.driver.execute_script("flutter:clickElement", self.by_key(key))

    def tap_text(self, text: str, timeout: int = None) -> None:
        self.wait_for_text(text, timeout)
        self.driver.execute_script("flutter:clickElement", self.by_text(text))

    def enter_text_by_key(self, key: str, value: str, timeout: int = None) -> None:
        self.wait_for_key(key, timeout)
        self.driver.execute_script("flutter:enterText", self.by_key(key), value)

    def get_text_by_key(self, key: str, timeout: int = None) -> str:
        """Only call this on Text/EditableText-backed widgets (e.g. text
        fields) — see module docstring."""
        self.wait_for_key(key, timeout)
        return self.driver.execute_script("flutter:getText", self.by_key(key))

    # ── Screen identity (no page_source, see module docstring) ────────
    def current_screen_contains(self, marker_text: str, timeout: int = None) -> bool:
        # Default changed from SHORT_TIMEOUT (5s) to DEFAULT_TIMEOUT (15s).
        # SHORT_TIMEOUT is correctly used by the handful of tests that pass
        # it explicitly for fast-fail negative checks ("this error text is
        # NOT present") — those all pass their own `timeout=` already, so
        # they're unaffected. But every is_loaded() across every page
        # object relies on THIS unqualified default for full screen-
        # transition checks, and 5s was consistently too tight for
        # transitions on this CI emulator (in-app navigation into Scanner,
        # cold relaunch, etc.) — confirmed against raw CI logs showing
        # is_loaded() checks exhausting a 5s window with repeated 500s
        # right up to the deadline, not intermittent flakiness.
        return self.wait_for_text(marker_text, timeout or config.DEFAULT_TIMEOUT)

    def is_on_screen(self, screen_name: str, timeout: int = None) -> bool:
        marker = config.ROUTE_TEXT_MARKERS[screen_name]
        return self.current_screen_contains(marker, timeout)

    # ── Adb-backed capabilities the Flutter engine doesn't implement ──
    def background_and_resume(self, seconds: float = 2.0) -> None:
        adb_helpers.background_app(seconds)

    def go_offline(self) -> None:
        adb_helpers.set_network_offline()

    def go_online(self) -> None:
        adb_helpers.set_network_online()

    def swipe_up(self, x: int = 540, y_start: int = 1600, y_end: int = 600) -> None:
        adb_helpers.swipe(x, y_start, y_end)

    # ── Failure capture ─────────────────────────────────────────────
    def capture_failure(self, name: str) -> None:
        """Guards against a signal.alarm firing WHILE blocked inside a
        screenshot call — catches BaseException (not just Exception) so
        the whole shard can't die with INTERNALERROR mid-capture, and
        always disarms any pending alarm before returning control."""
        import os
        os.makedirs(config.SCREENSHOTS_DIR, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
        try:
            self.driver.get_screenshot_as_file(
                os.path.join(config.SCREENSHOTS_DIR, f"{safe_name}.png")
            )
        except BaseException:
            pass
        finally:
            try:
                signal.alarm(0)
            except (ValueError, AttributeError):
                pass  # signal.alarm is POSIX-only / main-thread-only
        try:
            adb_helpers.pull_logcat(os.path.join(config.LOGS_DIR, f"{safe_name}.log"))
        except Exception:
            pass
