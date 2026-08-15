"""
CATEGORY: Offline Handling

This app is offline-first for its core loop: scan history and profile
are stored on-device via Drift (SQLite), and OCR runs on-device via
google_mlkit_text_recognition — no backend round-trip is required to
scan, view history, or edit a profile. These tests verify that offline
promise holds for every screen that should not need connectivity.
"""

import time

import pytest

from utils import adb_helpers


def test_home_loads_while_offline(reset_to_guest_home, home_page):
    """Home screen renders fully while the device has no network."""
    adb_helpers.set_network_offline()
    try:
        home_page.background_and_resume(1)
        assert home_page.is_loaded()
    finally:
        adb_helpers.set_network_online()


def test_history_loads_while_offline(reset_to_guest_home, main_shell, history_page):
    """History tab (backed entirely by local Drift DB) loads while offline."""
    adb_helpers.set_network_offline()
    try:
        main_shell.go_history()
        assert history_page.is_empty_state_visible() or history_page.is_list_visible()
    finally:
        adb_helpers.set_network_online()


def test_profile_editable_while_offline(reset_to_guest_home, main_shell, profile_page):
    """Profile form (allergy/condition/goal chips, name field, save) is fully
    usable while offline."""
    adb_helpers.set_network_offline()
    try:
        main_shell.go_profile()
        profile_page.enter_name("Offline Test User")
        profile_page.toggle_chip("allergies", "Dairy")
        profile_page.save()
        assert profile_page.is_loaded()
    finally:
        adb_helpers.set_network_online()


def test_manual_scan_entry_works_while_offline(reset_to_guest_home, home_page, scanner_page):
    """Manual ingredient entry (on-device only) works with no network."""
    adb_helpers.set_network_offline()
    try:
        home_page.tap_scan_card()
        scanner_page.open_manual_entry()
        scanner_page.enter_manual_ingredients("Water, Salt, Sugar")
        assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)
    finally:
        adb_helpers.set_network_online()


@pytest.mark.parametrize("i", range(1, 9))
def test_offline_online_transition_mid_session_is_stable(reset_to_guest_home, main_shell, home_page, i):
    """Flipping network state on/off 8 times mid-session never crashes the
    app or breaks navigation (checks connectivity_plus stream handling in
    scan_provider.dart doesn't throw on rapid state changes)."""
    adb_helpers.set_network_offline()
    time.sleep(0.5)
    adb_helpers.set_network_online()
    main_shell.go_home()
    assert home_page.is_loaded(), f"iteration {i}: home broke after connectivity flap"


def test_guest_login_works_fully_offline(auth_page, home_page):
    """A brand-new guest session can be created with zero connectivity."""
    adb_helpers.clear_app_data()
    adb_helpers.set_network_offline()
    adb_helpers.relaunch_app()
    time.sleep(3)
    try:
        if auth_page.is_loaded():
            auth_page.continue_as_guest()
        assert home_page.is_loaded()
    finally:
        adb_helpers.set_network_online()


@pytest.mark.parametrize("i", range(1, 9))
def test_bottom_nav_fully_functional_offline(reset_to_guest_home, main_shell, i):
    """All three bottom-nav tabs remain reachable across 8 offline navigation
    cycles — nothing in the main shell silently depends on connectivity."""
    adb_helpers.set_network_offline()
    try:
        main_shell.go_history()
        main_shell.go_profile()
        main_shell.go_home()
        assert main_shell.is_visible(), f"iteration {i}: nav broke offline"
    finally:
        adb_helpers.set_network_online()
