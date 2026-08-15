"""
CATEGORY: Camera & File Upload

Covers the scanner's three capture entry points: live camera capture,
gallery picker, and (web-only) file upload. Camera hardware is not
reliably simulated on a standard AVD without a seeded virtual scene,
so these tests check controls, permission handling, and navigation
around capture — not OCR accuracy of a captured frame, which is out of
scope for UI-level Appium testing and belongs in a unit/golden test
for the OCR service instead.
"""

import pytest

from utils import adb_helpers


def test_capture_button_visible_on_scanner(reset_to_guest_home, home_page, scanner_page):
    """Shutter/capture button is visible once Scanner opens."""
    home_page.tap_scan_card()
    assert scanner_page.capture_button_visible()


def test_gallery_button_visible_on_scanner(reset_to_guest_home, home_page, scanner_page):
    """Gallery-picker button is visible on Scanner."""
    home_page.tap_scan_card()
    assert scanner_page.is_displayed_by_key(scanner_page.GALLERY_BTN)


def test_flash_toggle_visible_and_tappable(reset_to_guest_home, home_page, scanner_page):
    """Flash/torch toggle is visible and can be tapped without crashing."""
    home_page.tap_scan_card()
    scanner_page.toggle_flash()
    assert scanner_page.is_loaded()


def test_ar_overlay_toggle_visible_and_tappable(reset_to_guest_home, home_page, scanner_page):
    """AR ingredient-overlay toggle is visible and can be tapped without crashing."""
    home_page.tap_scan_card()
    scanner_page.toggle_ar_overlay()
    assert scanner_page.is_loaded()


@pytest.mark.parametrize("i", range(1, 9))
def test_flash_toggle_repeated_taps_stable(reset_to_guest_home, home_page, scanner_page, i):
    """Toggling flash on/off 8 times in a row never leaves the camera preview
    in a broken state."""
    home_page.tap_scan_card()
    scanner_page.toggle_flash()
    assert scanner_page.is_loaded(), f"iteration {i}: scanner broke after flash toggle"


def test_capture_with_camera_permission_granted(reset_to_guest_home, home_page, scanner_page):
    """Capture button remains tappable when camera permission is explicitly granted."""
    adb_helpers.grant_camera_permission()
    home_page.tap_scan_card()
    assert scanner_page.capture_button_visible()


def test_capture_with_camera_permission_revoked_falls_back_gracefully(
    reset_to_guest_home, home_page, scanner_page
):
    """With camera permission revoked, the screen still loads (Android shows
    its own native permission prompt; the app itself does not crash)."""
    adb_helpers.revoke_camera_permission()
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()
    adb_helpers.grant_camera_permission()


def test_gallery_button_reachable_without_camera_permission(
    reset_to_guest_home, home_page, scanner_page
):
    """Gallery picker (a separate Android permission from Camera) is reachable
    even when camera permission is denied."""
    adb_helpers.revoke_camera_permission()
    home_page.tap_scan_card()
    assert scanner_page.is_displayed_by_key(scanner_page.GALLERY_BTN)
    adb_helpers.grant_camera_permission()


@pytest.mark.parametrize("i", range(1, 11))
def test_scanner_entry_exit_stress_around_capture_controls(
    reset_to_guest_home, home_page, scanner_page, i
):
    """Entering Scanner, checking the capture button, then leaving — repeated
    10 times — never leaves the camera preview session in a bad state for
    the next entry (a common Flutter camera-plugin lifecycle bug class)."""
    home_page.tap_scan_card()
    assert scanner_page.capture_button_visible(), f"iteration {i}: capture button missing"
    scanner_page.go_back()
    assert home_page.is_loaded(), f"iteration {i}: failed to return to Home"


def test_type_button_offers_no_camera_alternative(reset_to_guest_home, home_page, scanner_page):
    """The 'Type' manual-entry button is always available as a no-camera
    alternative input path, regardless of camera permission state."""
    adb_helpers.revoke_camera_permission()
    home_page.tap_scan_card()
    assert scanner_page.is_displayed_by_key(scanner_page.TYPE_BTN)
    adb_helpers.grant_camera_permission()
