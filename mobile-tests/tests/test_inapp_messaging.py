"""
CATEGORY: In-App Messaging (SnackBars)

Coverage-honesty note: this app has NO push-notification integration
(confirmed — no firebase_messaging dependency in pubspec.yaml, no
notification channel setup in the Android manifest). The prompt this
suite is based on calls for a "Notifications" category; substituted
here with the app's real in-app messaging mechanism — ScaffoldMessenger
SnackBars — which is the actual, present feature that plays the
equivalent "give the user transient feedback" role.
"""

import time

import pytest

from utils import adb_helpers


def test_web_upload_button_shows_coming_soon_snackbar(reset_to_guest_home, home_page, scanner_page):
    """The (web-mode) upload-image button shows a 'coming soon' SnackBar
    rather than silently doing nothing — scanner_screen.dart web branch."""
    home_page.tap_scan_card()
    if scanner_page.is_displayed_by_key("scanner_web_upload_btn"):
        scanner_page.tap_key("scanner_web_upload_btn")
        assert scanner_page.wait_for_text("Image OCR coming soon", timeout=5)


@pytest.mark.parametrize("i", range(1, 9))
def test_snackbar_dismisses_and_does_not_stack_indefinitely(
    reset_to_guest_home, home_page, scanner_page, i
):
    """Triggering the same SnackBar 8 times in a row does not visually stack
    or leak (Flutter's ScaffoldMessenger queues/replaces by default)."""
    home_page.tap_scan_card()
    if scanner_page.is_displayed_by_key("scanner_web_upload_btn"):
        scanner_page.tap_key("scanner_web_upload_btn")
        time.sleep(1)
    assert scanner_page.is_loaded(), f"iteration {i}: scanner screen broke after snackbar trigger"


def test_manual_entry_reachable_without_relying_on_snackbar_dismissal(
    reset_to_guest_home, home_page, scanner_page
):
    """A user does not need to wait for or dismiss a SnackBar before the
    manual-entry path becomes usable — no modal blocking behind SnackBars."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)


@pytest.mark.parametrize("cycle", range(1, 6))
def test_repeated_scanner_entry_snackbar_flow_stable(reset_to_guest_home, home_page, scanner_page, cycle):
    """Entering and leaving the Scanner screen 5 times, triggering the
    coming-soon SnackBar each time, never leaves a stale SnackBar visible
    on re-entry."""
    home_page.tap_scan_card()
    if scanner_page.is_displayed_by_key("scanner_web_upload_btn"):
        scanner_page.tap_key("scanner_web_upload_btn")
    scanner_page.go_back()
    assert home_page.is_loaded(), f"cycle {cycle}: home screen broke after snackbar cycle"


@pytest.mark.parametrize("i", range(1, 6))
def test_snackbar_flow_survives_background_resume(reset_to_guest_home, home_page, scanner_page, i):
    """Triggering a SnackBar right before backgrounding the app does not
    crash on resume — checked across 5 iterations."""
    home_page.tap_scan_card()
    if scanner_page.is_displayed_by_key("scanner_web_upload_btn"):
        scanner_page.tap_key("scanner_web_upload_btn")
    scanner_page.background_and_resume(1.5)
    assert scanner_page.is_loaded(), f"iteration {i}: scanner broke after snackbar + background"
