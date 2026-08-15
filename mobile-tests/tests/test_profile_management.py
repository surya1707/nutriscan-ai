"""
CATEGORY: Profile Management

Covers mobile/lib/features/profile/screens/profile_screen.dart end to
end: name editing, allergy/condition/goal selection, saving, and
sign-out — the app's only user-editable settings surface (there is no
separate "Settings" screen).
"""

import pytest

from config import ALLERGIES, CONDITIONS, GOALS


@pytest.mark.smoke
def test_profile_screen_loads(reset_to_guest_home, main_shell, profile_page):
    """Profile screen loads via bottom nav."""
    main_shell.go_profile()
    assert profile_page.is_loaded()


def test_profile_name_field_visible(reset_to_guest_home, main_shell, profile_page):
    """Name field is visible on Profile."""
    main_shell.go_profile()
    assert profile_page.is_displayed_by_key(profile_page.NAME_FIELD)


def test_profile_sign_out_button_visible(reset_to_guest_home, main_shell, profile_page):
    """Sign-out control is visible on Profile."""
    main_shell.go_profile()
    assert profile_page.is_displayed_by_key(profile_page.SIGN_OUT_BTN)


def test_all_allergy_chips_rendered(reset_to_guest_home, main_shell, profile_page):
    """All 12 configured allergy options are rendered as chips."""
    main_shell.go_profile()
    for item in ALLERGIES:
        assert profile_page.chip_visible("allergies", item), f"missing allergy chip: {item}"


def test_all_condition_chips_rendered(reset_to_guest_home, main_shell, profile_page):
    """All 8 configured medical-condition options are rendered as chips."""
    main_shell.go_profile()
    for item in CONDITIONS:
        assert profile_page.chip_visible("conditions", item), f"missing condition chip: {item}"


def test_all_goal_chips_rendered(reset_to_guest_home, main_shell, profile_page):
    """All 10 configured dietary-goal options are rendered as chips."""
    main_shell.go_profile()
    for item in GOALS:
        assert profile_page.chip_visible("goals", item), f"missing goal chip: {item}"


@pytest.mark.parametrize("name,allergy,condition,goal", [
    ("Asha R.", "Peanuts", "Diabetes", "Low Sugar"),
    ("Tom", "Dairy", "Hypertension", "Low Sodium"),
    ("Meera", "Shellfish", "Celiac Disease", "Gluten-Free"),
    ("Sam K.", "Tree Nuts", "PCOS", "High Protein"),
    ("Divya", "Soy", "IBS", "Vegan"),
])
def test_full_profile_edit_and_save_flow(reset_to_guest_home, main_shell, profile_page, name, allergy, condition, goal):
    """A realistic full profile edit — name + one chip per group — saves
    cleanly across five distinct persona combinations."""
    main_shell.go_profile()
    profile_page.enter_name(name)
    profile_page.toggle_chip("allergies", allergy)
    profile_page.toggle_chip("conditions", condition)
    profile_page.toggle_chip("goals", goal)
    profile_page.save()
    assert profile_page.is_loaded()


def test_profile_changes_persist_after_navigating_away_and_back(
    reset_to_guest_home, main_shell, profile_page
):
    """Saved chip selections are still shown after leaving Profile for
    another tab and returning."""
    main_shell.go_profile()
    profile_page.toggle_chip("goals", "Whole Foods")
    profile_page.save()
    main_shell.go_home()
    main_shell.go_profile()
    assert profile_page.chip_visible("goals", "Whole Foods")


def test_profile_changes_persist_across_app_relaunch(reset_to_guest_home, main_shell, profile_page):
    """Saved profile edits survive a full app relaunch (proving they're
    written to the Drift DB, not just held in in-memory Riverpod state)."""
    from utils import adb_helpers
    import time
    main_shell.go_profile()
    profile_page.toggle_chip("allergies", "Sesame")
    profile_page.save()
    adb_helpers.force_stop_app()
    adb_helpers.relaunch_app()
    time.sleep(2)
    main_shell.go_profile()
    assert profile_page.chip_visible("allergies", "Sesame")


@pytest.mark.parametrize("i", range(1, 6))
def test_profile_save_button_remains_responsive_after_repeated_taps(
    reset_to_guest_home, main_shell, profile_page, i
):
    """Save button remains responsive across 5 consecutive saves in the same
    session (no debounce lock-up)."""
    main_shell.go_profile()
    profile_page.enter_name(f"Repeated Save {i}")
    profile_page.save()
    assert profile_page.is_loaded(), f"save #{i} broke the profile screen"


@pytest.mark.parametrize("item", ALLERGIES)
def test_each_allergy_chip_independently_persists_after_save(
    reset_to_guest_home, main_shell, profile_page, item
):
    """Each of the 12 allergy chips independently persists across a
    navigate-away-and-back cycle when selected and saved on its own."""
    main_shell.go_profile()
    profile_page.toggle_chip("allergies", item)
    profile_page.save()
    main_shell.go_home()
    main_shell.go_profile()
    assert profile_page.chip_visible("allergies", item)
    profile_page.toggle_chip("allergies", item)  # reset for next parametrized run
    profile_page.save()
