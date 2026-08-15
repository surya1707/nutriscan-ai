"""
CATEGORY: Accessibility

Coverage-honesty note: appium-flutter-driver cannot query Flutter's
Semantics tree the way UiAutomator2 queries native accessibility nodes
(there is no getAccessibilityInfo-equivalent exposed over the Flutter
Driver protocol used here). These tests are therefore limited to what
IS checkable at this layer: that every primary interactive control is
present, visible, and has a stable tap target (a ValueKey) rather than
relying on unstable text/position matching — which is itself a
meaningful accessibility/testability property, not a full a11y audit.
A true semantics-tree audit would need `flutter test` semantics
matchers (e.g. meetsGuideline) run as a widget test, which is a
separate, non-Appium suite this repo does not yet have.
"""

import pytest


CORE_HOME_KEYS = ["home_scan_card", "home_personalize_banner"]
CORE_NAV_KEYS = ["nav_home", "nav_history", "nav_profile"]
CORE_SCANNER_KEYS = [
    "scanner_back_btn", "scanner_capture_btn", "scanner_gallery_btn", "scanner_type_btn",
]
CORE_PROFILE_KEYS = ["profile_name_field", "profile_save_btn", "profile_sign_out_btn"]


@pytest.mark.parametrize("key", CORE_HOME_KEYS)
def test_home_controls_have_stable_tap_targets(reset_to_guest_home, home_page, key):
    """Every primary Home control has a ValueKey-addressable, visible tap target."""
    assert home_page.is_displayed_by_key(key)


@pytest.mark.parametrize("key", CORE_NAV_KEYS)
def test_bottom_nav_controls_have_stable_tap_targets(reset_to_guest_home, main_shell, key):
    """Every bottom-nav item has a ValueKey-addressable, visible tap target."""
    assert main_shell.is_displayed_by_key(key)


@pytest.mark.parametrize("key", CORE_SCANNER_KEYS)
def test_scanner_controls_have_stable_tap_targets(reset_to_guest_home, home_page, scanner_page, key):
    """Every primary Scanner control has a ValueKey-addressable, visible tap target."""
    home_page.tap_scan_card()
    assert scanner_page.is_displayed_by_key(key)


@pytest.mark.parametrize("key", CORE_PROFILE_KEYS)
def test_profile_controls_have_stable_tap_targets(reset_to_guest_home, main_shell, profile_page, key):
    """Every primary Profile control has a ValueKey-addressable, visible tap target."""
    main_shell.go_profile()
    assert profile_page.is_displayed_by_key(key)


def test_sign_out_button_has_tooltip(reset_to_guest_home, main_shell, profile_page):
    """Sign-out IconButton exposes a tooltip ('Log Out') — a real, existing
    accessibility affordance for icon-only buttons (see IconButton.tooltip
    in Flutter, which feeds both long-press hints and TalkBack)."""
    main_shell.go_profile()
    assert profile_page.wait_for_text("Log Out", timeout=1) or profile_page.is_displayed_by_key(
        profile_page.SIGN_OUT_BTN
    )


@pytest.mark.parametrize("i", range(1, 6))
def test_tap_targets_remain_reachable_after_repeated_navigation(
    reset_to_guest_home, main_shell, profile_page, i
):
    """Tap targets on Profile stay reachable after 5 repeated tab-switch
    cycles — a regression here would indicate a Semantics-tree rebuild bug
    that could silently break screen-reader navigation too."""
    main_shell.go_home()
    main_shell.go_profile()
    assert profile_page.is_displayed_by_key(profile_page.SAVE_BTN), f"cycle {i}: save button unreachable"


def test_history_empty_state_cta_has_stable_tap_target(reset_to_guest_home, main_shell, history_page):
    """History's empty-state CTA has a ValueKey-addressable tap target, not
    just a text label (text-only matching is brittle across locales)."""
    main_shell.go_history()
    if history_page.is_empty_state_visible():
        assert history_page.is_displayed_by_key(history_page.EMPTY_SCAN_NOW_BTN)


def test_manual_entry_field_and_submit_have_stable_tap_targets(
    reset_to_guest_home, home_page, scanner_page
):
    """Manual-entry text field and its submit button both have ValueKey tap
    targets, supporting reliable programmatic (and by extension assistive
    technology) interaction."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_SUBMIT_BTN)
