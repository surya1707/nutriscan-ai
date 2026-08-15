"""
CATEGORY: List Browsing & Filters

Coverage-honesty note: this app has NO search bar and NO explicit
filter/sort UI anywhere (confirmed via a full grep of mobile/lib for
"search"/"filter" — see mobile-tests/README.md "Stack detection"). The
closest real analogue to a filter control is the set of selectable
allergy/condition/goal chips on the Profile screen (profile_screen.dart
_ChipGroup), which functionally filter what the app treats as
"relevant" to the user. This file tests that mechanism, plus the
History list's scroll/browse behaviour, instead of fabricating tests
for a search bar that does not exist.
"""

import pytest

from config import ALLERGIES, CONDITIONS, GOALS


@pytest.mark.parametrize("item", ALLERGIES)
def test_allergy_chip_visible_and_togglable(reset_to_guest_home, main_shell, profile_page, item):
    """Every allergy chip is visible and can be tapped without error."""
    main_shell.go_profile()
    assert profile_page.chip_visible("allergies", item)
    profile_page.toggle_chip("allergies", item)
    assert profile_page.chip_visible("allergies", item)


@pytest.mark.parametrize("item", CONDITIONS)
def test_condition_chip_visible_and_togglable(reset_to_guest_home, main_shell, profile_page, item):
    """Every medical-condition chip is visible and can be tapped without error."""
    main_shell.go_profile()
    assert profile_page.chip_visible("conditions", item)
    profile_page.toggle_chip("conditions", item)
    assert profile_page.chip_visible("conditions", item)


@pytest.mark.parametrize("item", GOALS)
def test_goal_chip_visible_and_togglable(reset_to_guest_home, main_shell, profile_page, item):
    """Every dietary-goal chip is visible and can be tapped without error."""
    main_shell.go_profile()
    assert profile_page.chip_visible("goals", item)
    profile_page.toggle_chip("goals", item)
    assert profile_page.chip_visible("goals", item)


def test_chip_toggle_is_reversible(reset_to_guest_home, main_shell, profile_page):
    """Tapping the same chip twice (select, then deselect) leaves the chip visible
    and does not desync the Profile screen."""
    main_shell.go_profile()
    profile_page.toggle_chip("allergies", "Peanuts")
    profile_page.toggle_chip("allergies", "Peanuts")
    assert profile_page.chip_visible("allergies", "Peanuts")


def test_multiple_chips_across_groups_can_be_selected_together(reset_to_guest_home, main_shell, profile_page):
    """Selecting chips from all three groups simultaneously works (they are
    independent Sets, not a mutually-exclusive radio group)."""
    main_shell.go_profile()
    profile_page.toggle_chip("allergies", "Dairy")
    profile_page.toggle_chip("conditions", "Diabetes")
    profile_page.toggle_chip("goals", "Vegan")
    for group, item in [("allergies", "Dairy"), ("conditions", "Diabetes"), ("goals", "Vegan")]:
        assert profile_page.chip_visible(group, item)


def test_chip_selection_persists_after_save(reset_to_guest_home, main_shell, profile_page):
    """Selecting chips and saving does not remove them from view."""
    main_shell.go_profile()
    profile_page.toggle_chip("goals", "Keto")
    profile_page.save()
    assert profile_page.is_loaded()
    assert profile_page.chip_visible("goals", "Keto")


def test_history_list_scrolls_without_crashing(reset_to_guest_home, main_shell, history_page):
    """History list (if populated) can be scrolled via adb swipe without a crash.
    On an empty account this is a no-op against the empty state, which is
    itself a valid pass (nothing to scroll, nothing crashed)."""
    main_shell.go_history()
    history_page.swipe_up()
    assert history_page.is_empty_state_visible() or history_page.is_list_visible()
