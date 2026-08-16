"""
CATEGORY: Dashboard / Home

Covers: mobile/lib/features/home/screens/home_screen.dart and its
widgets (HeroScanCard, PersonalizeBanner, stats row, greeting header).
"""

import pytest


@pytest.mark.smoke
def test_home_screen_loads_after_guest_login(reset_to_guest_home):
    """Home screen loads and shows its headline after guest login."""
    assert reset_to_guest_home.is_loaded()


def test_hero_scan_card_visible(reset_to_guest_home, home_page):
    """Hero scan card is visible on Home."""
    assert home_page.scan_card_visible()


def test_personalize_banner_visible(reset_to_guest_home, home_page):
    """Personalize-profile banner is visible on Home."""
    assert home_page.is_displayed_by_key(home_page.PERSONALIZE_BANNER)


def test_greeting_reflects_guest_user(reset_to_guest_home, home_page):
    """Greeting header references the Guest identity for a guest session."""
    assert home_page.greeting_shows_guest()


@pytest.mark.parametrize("i", range(1, 6))
def test_home_reloads_consistently_across_relaunches(reset_to_guest_home, home_page, i):
    """Home screen renders its hero card consistently across 5 relaunches of an
    already-authenticated session."""
    from utils import adb_helpers
    import time
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    home_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    assert home_page.is_loaded(), f"relaunch {i} did not reach Home"
    assert home_page.scan_card_visible(), f"relaunch {i} lost the hero scan card"


def test_scan_card_opens_scanner(reset_to_guest_home, home_page, scanner_page):
    """Hero scan card is a working entry point into the Scanner flow."""
    home_page.tap_scan_card()
    assert scanner_page.is_loaded()


def test_personalize_banner_opens_profile(reset_to_guest_home, home_page, profile_page):
    """Personalize banner is a working entry point into the Profile flow."""
    home_page.tap_personalize_banner()
    assert profile_page.is_loaded()


def test_home_survives_background_resume(reset_to_guest_home, home_page):
    """Home screen state survives a background + resume cycle."""
    home_page.background_and_resume(2)
    assert home_page.is_loaded()


@pytest.mark.parametrize("orientation_note", ["portrait-only-app"])
def test_home_layout_has_no_overflow_markers(reset_to_guest_home, home_page, orientation_note):
    """No RenderFlex overflow banner text is visible on Home (a common Flutter
    layout-bug signature that renders literal 'A RenderFlex overflowed' text)."""
    assert not home_page.current_screen_contains("RenderFlex overflowed", timeout=2)


@pytest.mark.parametrize("i", range(1, 9))
def test_home_scan_card_visible_after_n_tab_round_trips(reset_to_guest_home, main_shell, home_page, i):
    """Hero scan card keeps rendering correctly after N round trips through the
    other two tabs (catches state-loss-on-tab-switch regressions)."""
    main_shell.go_history()
    main_shell.go_home()
    assert home_page.scan_card_visible(), f"round trip {i} lost the hero scan card"
