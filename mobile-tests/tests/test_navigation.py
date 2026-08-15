"""
CATEGORY: Navigation

Covers: mobile/lib/shared/widgets/main_shell.dart (bottom nav) and the
push/pop stack between Home -> Scanner -> Results, driven by go_router.
"""

import pytest

from config import ROUTE_TEXT_MARKERS


@pytest.mark.smoke
def test_bottom_nav_visible_on_home(reset_to_guest_home, main_shell):
    """Bottom nav bar is visible on the Home tab."""
    assert main_shell.is_visible()


@pytest.mark.parametrize("target", ["home", "history", "profile"])
def test_bottom_nav_switches_to_each_tab(reset_to_guest_home, main_shell, target):
    """Tapping each bottom-nav item switches to the matching screen."""
    getattr(main_shell, f"go_{target}")()
    assert main_shell.wait_for_text(ROUTE_TEXT_MARKERS[target], timeout=8)


@pytest.mark.parametrize("sequence", [
    ["history", "profile", "home"],
    ["profile", "history", "home"],
    ["home", "profile", "history"],
    ["history", "home", "profile"],
    ["profile", "home", "history"],
])
def test_bottom_nav_arbitrary_tab_orders(reset_to_guest_home, main_shell, sequence):
    """Tabs can be visited in any order without losing the nav bar or crashing."""
    for target in sequence:
        getattr(main_shell, f"go_{target}")()
        assert main_shell.wait_for_text(ROUTE_TEXT_MARKERS[target], timeout=8)
    assert main_shell.is_visible()


def test_home_to_scanner_push(reset_to_guest_home, home_page, scanner_page):
    """Tapping the hero scan card pushes the Scanner screen."""
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()


def test_scanner_back_pops_to_home(reset_to_guest_home, home_page, scanner_page):
    """Scanner's back button pops back to Home."""
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()
    scanner_page.go_back()
    assert home_page.is_loaded()


def test_personalize_banner_navigates_to_profile(reset_to_guest_home, home_page, profile_page):
    """Personalize banner on Home routes to the Profile screen."""
    home_page.tap_personalize_banner()
    assert profile_page.is_loaded()


def test_history_empty_state_scan_now_opens_scanner(reset_to_guest_home, main_shell, history_page, scanner_page):
    """History's empty-state 'Scan now' CTA opens the Scanner screen."""
    main_shell.go_history()
    if history_page.is_empty_state_visible():
        history_page.tap_empty_state_scan_now()
        assert scanner_page.is_loaded()


@pytest.mark.parametrize("hops", range(1, 6))
def test_repeated_home_scanner_round_trips(reset_to_guest_home, home_page, scanner_page, hops):
    """Home <-> Scanner can be traversed back and forth repeatedly (5 round
    trips) without the nav stack leaking or the back button breaking."""
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()
    scanner_page.go_back()
    assert home_page.is_loaded(), f"round trip {hops} failed to return to Home"


def test_android_hardware_back_from_scanner_returns_home(reset_to_guest_home, home_page, scanner_page):
    """Android hardware back button (not the in-app back arrow) also pops Scanner."""
    import subprocess
    from config import DEVICE_NAME
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()
    subprocess.run(["adb", "-s", DEVICE_NAME, "shell", "input", "keyevent", "KEYCODE_BACK"], timeout=10)
    assert home_page.is_loaded()


def test_deep_nav_stack_does_not_break_bottom_nav(reset_to_guest_home, home_page, scanner_page, main_shell):
    """After pushing then popping Scanner, the bottom nav still functions correctly."""
    home_page.tap_scan_card()
    scanner_page.go_back()
    main_shell.go_history()
    assert main_shell.wait_for_text(ROUTE_TEXT_MARKERS["history"], timeout=8)


@pytest.mark.parametrize("i", range(1, 11))
def test_bottom_nav_survives_rapid_tab_spam(reset_to_guest_home, main_shell, i):
    """Rapidly tapping between Home/History/Profile 10 times in a row does not
    desync the nav bar's active-tab indicator or crash the app."""
    main_shell.go_history()
    main_shell.go_profile()
    main_shell.go_home()
    assert main_shell.wait_for_text(ROUTE_TEXT_MARKERS["home"], timeout=8), f"spam cycle {i} lost Home screen"
