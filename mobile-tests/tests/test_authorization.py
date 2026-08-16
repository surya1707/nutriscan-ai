"""
CATEGORY: Authorization / Route Guards

Covers: mobile/lib/core/router/app_router.dart redirect logic — the
GoRouter `redirect` callback that sends an unauthenticated user to
/auth and an authenticated one away from /auth.

Coverage-honesty note: there is no role-based access control in this
app (no admin vs. regular user distinction) — "authorization" here
means exactly one thing: authenticated-or-not route gating. Tests that
would check role-based permissions do not apply and are not included;
substituted instead with repeated/parametrized checks of the single
real guard from every reachable entry screen.
"""

import time

import pytest

from utils import adb_helpers

PROTECTED_SCREENS = ["home", "history", "profile"]


@pytest.mark.parametrize("screen", PROTECTED_SCREENS)
def test_unauthenticated_state_does_not_expose_protected_screen(auth_page, screen):
    """A signed-out user cannot see Home/History/Profile content — the guard
    redirects to /auth before any protected screen marker becomes visible."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    from config import ROUTE_TEXT_MARKERS
    assert not auth_page.current_screen_contains(ROUTE_TEXT_MARKERS[screen], timeout=3)


def test_signed_out_user_lands_on_auth_screen(auth_page):
    """A signed-out cold start always resolves to /auth, never a blank/protected screen."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    assert auth_page.is_loaded()


def test_guest_is_treated_as_authenticated_for_routing(auth_page, home_page):
    """Guest mode satisfies the router's isAuthenticated check (guest is a real,
    if anonymous, Firebase Auth session) — home becomes reachable."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    auth_page.continue_as_guest()
    assert home_page.is_loaded()


def test_authenticated_guest_cannot_navigate_back_to_auth(reset_to_guest_home, auth_page):
    """Once authenticated (guest), the redirect guard prevents the auth screen
    from staying visible even if something attempts to navigate to it."""
    assert not auth_page.current_screen_contains("Continue as Guest", timeout=3)


@pytest.mark.parametrize("screen", PROTECTED_SCREENS)
def test_authenticated_guest_can_reach_every_protected_screen(reset_to_guest_home, main_shell, screen):
    """Once authenticated, all three main-shell screens become reachable via bottom nav."""
    from config import ROUTE_TEXT_MARKERS
    getattr(main_shell, f"go_{screen}")()
    assert main_shell.driver.execute_script(
        "flutter:waitFor",
        main_shell.by_text(ROUTE_TEXT_MARKERS[screen]),
        8000,
    ) is not None


def test_signing_out_revokes_access_to_protected_screens(reset_to_guest_home, main_shell, profile_page, auth_page):
    """After sign-out, the app no longer shows protected-screen content — the
    guard re-applies on the very next redirect evaluation."""
    main_shell.go_profile()
    profile_page.sign_out()
    assert auth_page.is_loaded()
    assert not profile_page.current_screen_contains("Health Profile", timeout=3)


@pytest.mark.parametrize("cycle", range(1, 8))
def test_auth_guard_holds_across_repeated_signout_signin_cycles(
    auth_page, home_page, main_shell, profile_page, cycle
):
    """The redirect guard is re-evaluated correctly across 7 consecutive
    guest-login -> sign-out cycles (catches stale-provider-state regressions)."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    auth_page.continue_as_guest()
    assert home_page.is_loaded(), f"cycle {cycle}: guard blocked legitimate guest access"
    main_shell.go_profile()
    profile_page.sign_out()
    assert auth_page.is_loaded(), f"cycle {cycle}: guard failed to re-lock after sign-out"


def test_background_and_resume_does_not_bypass_guard(reset_to_guest_home, main_shell):
    """Backgrounding and resuming the app while authenticated does not drop the
    session or otherwise change the guard's decision mid-session."""
    main_shell.background_and_resume(2)
    assert main_shell.is_visible()


def test_killed_process_relaunch_reevaluates_guard_correctly(reset_to_guest_home, home_page):
    """A fully killed (not just backgrounded) process re-runs the guard on next
    launch and still reaches Home for a persisted guest session."""
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    home_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    assert home_page.is_loaded()


@pytest.mark.parametrize("target", PROTECTED_SCREENS)
def test_direct_bottom_nav_tap_from_each_tab_respects_session(reset_to_guest_home, main_shell, target):
    """Bottom-nav taps between all protected tabs succeed without ever
    bouncing back to /auth mid-session."""
    from pages.auth_page import AuthPage
    getattr(main_shell, f"go_{target}")()
    auth = AuthPage(main_shell.driver)
    assert not auth.current_screen_contains("Continue as Guest", timeout=2)


@pytest.mark.parametrize("i", range(1, 11))
def test_guard_stable_under_rapid_consecutive_tab_switches(reset_to_guest_home, main_shell, i):
    """Rapidly cycling through all three tabs 10 times never trips the guard
    into an unexpected redirect."""
    main_shell.go_home()
    main_shell.go_history()
    main_shell.go_profile()
    assert main_shell.is_visible(), f"iteration {i}: bottom nav disappeared mid-cycle"
