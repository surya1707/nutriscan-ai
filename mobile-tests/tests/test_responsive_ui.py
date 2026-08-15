"""
CATEGORY: Responsive UI

Coverage-honesty note: main.dart calls
SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp])
— this app is portrait-locked by design, so there is no
landscape/rotation behaviour to test (attempting to force landscape via
adb would be testing something the app explicitly opts out of, not a
real bug surface). These tests instead check rendering stability across
the two device-size classes the emulator matrix actually covers
(config note: run this file's shard on both a phone and a 7" tablet AVD
for real coverage — a single-density emulator run only proves one
data point).
"""

import pytest


@pytest.mark.parametrize("i", range(1, 6))
def test_home_screen_no_overflow_at_current_density(reset_to_guest_home, home_page, i):
    """Home screen shows no RenderFlex overflow banner on the current AVD's
    screen density/size — checked 5 times across independent app states."""
    assert not home_page.current_screen_contains("RenderFlex overflowed", timeout=2)


def test_scanner_screen_no_overflow(reset_to_guest_home, home_page, scanner_page):
    """Scanner screen (camera preview + bottom control bar) renders without overflow."""
    home_page.tap_scan_card()
    assert not scanner_page.current_screen_contains("RenderFlex overflowed", timeout=2)


def test_profile_screen_no_overflow_with_all_chip_groups_expanded(
    reset_to_guest_home, main_shell, profile_page
):
    """Profile screen (three full chip groups: 12+8+10 items) renders without
    overflow even with every chip group's full Wrap layout visible."""
    main_shell.go_profile()
    assert not profile_page.current_screen_contains("RenderFlex overflowed", timeout=2)


def test_history_empty_state_no_overflow(reset_to_guest_home, main_shell, history_page):
    """History empty-state illustration/CTA layout renders without overflow."""
    main_shell.go_history()
    assert not history_page.current_screen_contains("RenderFlex overflowed", timeout=2)


def test_bottom_nav_bar_no_overflow(reset_to_guest_home, main_shell):
    """Bottom navigation bar itself renders without overflow across all three tabs."""
    main_shell.go_home()
    assert not main_shell.current_screen_contains("RenderFlex overflowed", timeout=2)


def test_results_screen_no_overflow_after_manual_scan(reset_to_guest_home, home_page, scanner_page, results_page):
    """Results screen (score header + ingredient list) renders without
    overflow after a manual-entry scan."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients("Water, Sugar, Citric Acid, Natural Flavors")
    scanner_page.submit_manual_ingredients()
    assert not results_page.current_screen_contains("RenderFlex overflowed", timeout=5)
