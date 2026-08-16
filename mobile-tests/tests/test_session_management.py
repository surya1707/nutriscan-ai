"""
CATEGORY: Session Management

Covers persistence and teardown of the Firebase Auth session (guest or
otherwise) across process lifecycle events: background/resume, kill,
device-data-clear, and repeated sign-out.
"""

import time

import pytest

from utils import adb_helpers


def test_session_persists_across_background_resume(reset_to_guest_home, home_page):
    """A short background/resume cycle keeps the session alive."""
    home_page.background_and_resume(3)
    assert home_page.is_loaded()


def test_session_persists_across_process_kill(reset_to_guest_home, home_page):
    """A full process kill (not just background) still preserves the guest
    session, since Firebase Auth persists its token to disk."""
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    home_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    assert home_page.is_loaded()


def test_session_cleared_by_app_data_wipe(main_shell, auth_page):
    """Clearing app data is the one operation that genuinely ends the session
    (used deliberately by many other tests as a clean-slate fixture)."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    assert auth_page.is_loaded()


def test_sign_out_ends_session_immediately(reset_to_guest_home, main_shell, profile_page, auth_page):
    """Sign-out ends the session without requiring an app restart."""
    main_shell.go_profile()
    profile_page.sign_out()
    assert auth_page.is_loaded()


@pytest.mark.parametrize("bg_seconds", [1, 5, 15, 30])
def test_session_survives_varied_background_durations(reset_to_guest_home, home_page, bg_seconds):
    """Session survives across a range of background durations, from a brief
    app-switch (1s) up to a plausible phone-call-length interruption (30s)."""
    home_page.background_and_resume(bg_seconds)
    assert home_page.is_loaded()


@pytest.mark.parametrize("cycle", range(1, 9))
def test_session_stable_across_repeated_kill_relaunch_cycles(reset_to_guest_home, home_page, cycle):
    """Guest session survives 8 consecutive kill+relaunch cycles without ever
    silently dropping back to the auth screen."""
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    home_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    assert home_page.is_loaded(), f"cycle {cycle}: session was lost on relaunch"


def test_new_session_starts_clean_after_data_wipe_and_new_guest_login(
    main_shell, auth_page, home_page, history_page
):
    """After a data wipe, a brand-new guest login starts with an empty scan
    history — sessions are not cross-contaminated by a previous account's
    on-device data."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    home_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    if auth_page.is_loaded():
        auth_page.continue_as_guest()
    assert home_page.is_loaded()
    main_shell.go_history()
    assert history_page.is_empty_state_visible()


@pytest.mark.parametrize("i", range(1, 6))
def test_sign_out_then_re_login_as_guest_cycles_cleanly(
    auth_page, home_page, main_shell, profile_page, i
):
    """Sign-out followed immediately by a fresh guest login works reliably
    across 5 repeated cycles, with no leftover session state from the
    previous login affecting the new one."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    home_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    auth_page.continue_as_guest()
    assert home_page.is_loaded(), f"cycle {i}: guest login failed"
    main_shell.go_profile()
    profile_page.sign_out()
    assert auth_page.is_loaded(), f"cycle {i}: sign-out failed"
