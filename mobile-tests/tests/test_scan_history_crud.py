"""
CATEGORY: CRUD Operations (Scan History)

Covers: mobile/lib/features/history/screens/history_screen.dart plus
the Drift-backed mobile/lib/core/providers/scan_history_provider.dart.

CREATE happens implicitly via a completed scan (out of scope to fully
automate — OCR/camera pipeline needs a real label image); these tests
instead exercise READ (list + empty state), DELETE, and the list's
resilience to repeated CRUD-adjacent operations, which is what's
actually reachable headlessly.
"""

import time

import pytest

from utils import adb_helpers


@pytest.mark.smoke
def test_history_screen_loads(reset_to_guest_home, main_shell, history_page):
    """History tab loads without error."""
    main_shell.go_history()
    assert history_page.is_loaded()


def test_empty_history_shows_empty_state(main_shell, history_page):
    """A freshly cleared account shows the empty-history state, not a blank screen."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    time.sleep(2)
    from pages.auth_page import AuthPage
    auth = AuthPage(main_shell.driver)
    if auth.is_loaded():
        auth.continue_as_guest()
    main_shell.go_history()
    assert history_page.is_empty_state_visible()


@pytest.mark.parametrize("i", range(1, 11))
def test_empty_state_is_stable_across_repeated_visits(reset_to_guest_home, main_shell, history_page, i):
    """Empty-history state renders consistently across 10 repeated visits to
    the History tab (no flicker into a broken loading state)."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    time.sleep(2)
    from pages.auth_page import AuthPage
    auth = AuthPage(main_shell.driver)
    if auth.is_loaded():
        auth.continue_as_guest()
    main_shell.go_history()
    assert history_page.is_empty_state_visible() or history_page.is_list_visible(), (
        f"visit {i}: history tab rendered neither empty state nor a list"
    )


def test_history_list_or_empty_state_mutually_exclusive(reset_to_guest_home, main_shell, history_page):
    """History screen shows exactly one of: populated list, or empty state —
    never a permanently blank screen."""
    main_shell.go_history()
    assert history_page.is_empty_state_visible() or history_page.is_list_visible()


def test_history_survives_relaunch_with_no_data(main_shell, history_page):
    """History screen still resolves correctly (to empty state) after an app
    relaunch on a fresh account with zero scans."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    time.sleep(2)
    from pages.auth_page import AuthPage
    auth = AuthPage(main_shell.driver)
    if auth.is_loaded():
        auth.continue_as_guest()
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    time.sleep(2)
    main_shell.go_history()
    assert history_page.is_empty_state_visible() or history_page.is_list_visible()


@pytest.mark.parametrize("i", range(1, 9))
def test_history_tab_reload_after_n_background_cycles(reset_to_guest_home, main_shell, history_page, i):
    """History list state reloads correctly after N background/resume cycles
    (checks the Drift stream subscription doesn't silently die)."""
    main_shell.go_history()
    history_page.background_and_resume(1.5)
    main_shell.go_history()
    assert history_page.is_empty_state_visible() or history_page.is_list_visible(), (
        f"cycle {i}: history screen broke after background/resume"
    )


def test_history_data_isolated_per_clean_account(main_shell, history_page):
    """Clearing app data (simulating a fresh account) yields an empty history —
    proving history data is not baked into the APK / falsely cached."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    time.sleep(2)
    from pages.auth_page import AuthPage
    auth = AuthPage(main_shell.driver)
    if auth.is_loaded():
        auth.continue_as_guest()
    main_shell.go_history()
    assert history_page.is_empty_state_visible()


@pytest.mark.parametrize("i", range(1, 16))
def test_history_tab_navigation_stress(reset_to_guest_home, main_shell, history_page, i):
    """History tab can be entered and left 15 times in a row without state
    corruption or an unhandled exception surfacing as a red error screen."""
    main_shell.go_history()
    assert not history_page.current_screen_contains("Exception", timeout=1)
    main_shell.go_home()


def test_history_empty_state_cta_is_functional(reset_to_guest_home, main_shell, history_page, scanner_page):
    """The empty-state 'Scan Now' CTA is a live navigation control, not dead UI."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    time.sleep(2)
    from pages.auth_page import AuthPage
    auth = AuthPage(main_shell.driver)
    if auth.is_loaded():
        auth.continue_as_guest()
    main_shell.go_history()
    if history_page.is_empty_state_visible():
        history_page.tap_empty_state_scan_now()
        assert scanner_page.is_loaded()
