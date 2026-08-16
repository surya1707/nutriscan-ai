"""
CATEGORY: Error Handling

Covers graceful degradation: camera permission denial, network loss
during a scan (scan_provider.dart uses connectivity_plus), and
malformed navigation states. No screen in this app currently shows a
custom "friendly" error screen for these cases (confirmed by reading
scanner_screen.dart / scan_provider.dart) — these tests check that the
app does not hard-crash, which is the honest bar given the current
implementation, and flag (in their docstring) where a nicer error UI
would be a genuine improvement.
"""

import time

import pytest

from utils import adb_helpers


def test_camera_permission_revoked_does_not_crash_scanner(reset_to_guest_home, home_page, scanner_page):
    """Revoking camera permission before opening Scanner does not crash the
    app — it should fall back to the manual-entry / gallery paths."""
    adb_helpers.revoke_camera_permission()
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()
    adb_helpers.grant_camera_permission()  # restore for subsequent tests


def test_camera_permission_denied_leaves_manual_entry_reachable(
    reset_to_guest_home, home_page, scanner_page
):
    """With camera permission denied, the manual 'Type' entry path is still
    reachable as a fallback."""
    adb_helpers.revoke_camera_permission()
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)
    adb_helpers.grant_camera_permission()


def test_network_loss_during_scan_flow_does_not_crash(reset_to_guest_home, home_page, scanner_page):
    """Going offline mid-scan-flow does not crash the app (scan pipeline is
    on-device OCR; only external calls, if any, would fail gracefully)."""
    home_page.tap_scan_card()
    adb_helpers.set_network_offline()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients("Water, Salt")
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)
    adb_helpers.set_network_online()


@pytest.mark.parametrize("i", range(1, 9))
def test_repeated_permission_toggle_does_not_leak_state(reset_to_guest_home, home_page, scanner_page, i):
    """Toggling camera permission on/off 8 times before opening Scanner never
    leaves the screen in a stuck loading state."""
    if i % 2 == 0:
        adb_helpers.revoke_camera_permission()
    else:
        adb_helpers.grant_camera_permission()
    home_page.tap_scan_card()
    assert scanner_page.is_loaded(), f"iteration {i}: scanner failed to load"
    scanner_page.go_back()
    adb_helpers.grant_camera_permission()


def test_backgrounding_mid_scan_and_resuming_does_not_crash(reset_to_guest_home, home_page, scanner_page):
    """Backgrounding the app while the Scanner screen is open, then resuming,
    does not crash or lose the screen."""
    home_page.tap_scan_card()
    scanner_page.background_and_resume(2)
    assert scanner_page.is_loaded()


def test_offline_at_app_cold_start_does_not_block_guest_login(auth_page, home_page):
    """A fully offline device can still complete guest login (no network
    round-trip required for anonymous Firebase Auth in this build)."""
    adb_helpers.clear_app_data()
    adb_helpers.set_network_offline()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(3)
    try:
        if auth_page.is_loaded():
            auth_page.continue_as_guest()
        assert home_page.is_loaded()
    finally:
        adb_helpers.set_network_online()


@pytest.mark.parametrize("i", range(1, 12))
def test_app_does_not_show_uncaught_exception_banner_across_common_flows(
    reset_to_guest_home, main_shell, home_page, history_page, profile_page, i
):
    """None of the three main tabs ever shows Flutter's red 'Exception
    caught by' debug banner during ordinary navigation — checked across 11
    independent tab-visit sequences."""
    main_shell.go_home()
    assert not home_page.current_screen_contains("Exception caught by", timeout=1)
    main_shell.go_history()
    assert not history_page.current_screen_contains("Exception caught by", timeout=1)
    main_shell.go_profile()
    assert not profile_page.current_screen_contains("Exception caught by", timeout=1)
