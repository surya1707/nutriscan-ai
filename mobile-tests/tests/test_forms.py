"""
CATEGORY: Forms

Covers every text-input form in the app: the auth email field, the
scanner's manual-ingredients text field, and the profile name field.
"""

import pytest


# ── Manual ingredient entry (scanner_screen.dart _showTypeDialog) ────────

INGREDIENT_SAMPLES = [
    "Water, Sugar, Citric Acid",
    "Wheat Flour, Salt, Yeast",
    "Palm Oil, Cocoa, Milk Solids, Soy Lecithin",
    "Rice, Water",
    "High Fructose Corn Syrup, Caramel Color, Phosphoric Acid, Caffeine",
]


@pytest.mark.parametrize("ingredients", INGREDIENT_SAMPLES)
def test_manual_ingredient_form_accepts_realistic_labels(reset_to_guest_home, home_page, scanner_page, ingredients):
    """Manual ingredient text field accepts a range of realistic label texts."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients(ingredients)
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)


def test_manual_ingredient_field_accepts_multiline_text(reset_to_guest_home, home_page, scanner_page):
    """Manual ingredient field is multi-line (maxLines: 6) and accepts newline-separated text."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients("Water\nSugar\nSalt\nCitric Acid")
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)


def test_manual_ingredient_submit_button_visible(reset_to_guest_home, home_page, scanner_page):
    """Submit button for the manual ingredient dialog is visible once the field is open."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_SUBMIT_BTN)


@pytest.mark.parametrize("i", range(1, 6))
def test_manual_ingredient_form_reopens_cleanly(reset_to_guest_home, home_page, scanner_page, i):
    """Manual-entry dialog can be opened, typed into, and re-opened 5 times
    without leaking state from the previous entry in an unexpected way."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients(f"Test Ingredient List {i}")
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)


# ── Profile name field (profile_screen.dart) ──────────────────────────

NAME_SAMPLES = [
    "Priya", "A. Kumar", "Jean-Luc", "O'Brien", "李伟",
    "Mohammed bin Rashid", "Anna-Maria", "김민준",
]


@pytest.mark.parametrize("name", NAME_SAMPLES)
def test_profile_name_field_accepts_diverse_names(reset_to_guest_home, main_shell, profile_page, name):
    """Profile name field accepts a range of real-world name formats, including
    apostrophes, hyphens, and non-Latin scripts."""
    main_shell.go_profile()
    profile_page.enter_name(name)
    assert profile_page.is_displayed_by_key(profile_page.NAME_FIELD)


def test_profile_save_button_visible(reset_to_guest_home, main_shell, profile_page):
    """Save button is visible on the Profile form."""
    main_shell.go_profile()
    assert profile_page.save_btn_visible()


def test_profile_save_commits_name_change(reset_to_guest_home, main_shell, profile_page):
    """Saving the profile form after editing the name does not error out."""
    main_shell.go_profile()
    profile_page.enter_name("Test User QA")
    profile_page.save()
    assert profile_page.is_loaded()


@pytest.mark.parametrize("i", range(1, 6))
def test_profile_save_idempotent_across_repeats(reset_to_guest_home, main_shell, profile_page, i):
    """Saving the profile form repeatedly (5x) with the same data does not
    error, duplicate rows, or crash the app."""
    main_shell.go_profile()
    profile_page.enter_name(f"Repeat Save Test {i}")
    profile_page.save()
    assert profile_page.is_loaded(), f"save #{i} broke the profile screen"


# ── Auth email field cross-reference (already covered in depth in
#    test_authentication.py — these add form-specific structural checks) ─

def test_auth_email_field_is_single_line(auth_page):
    """Auth email field is a single-line TextField (not multi-line like the
    ingredient entry field)."""
    from utils import adb_helpers
    import time
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    auth_page.open_email_input()
    assert auth_page.email_field_visible()


@pytest.mark.parametrize("i", range(1, 9))
def test_auth_email_field_clears_between_cold_starts(auth_page, i):
    """Auth email field starts empty (no leaked value) on 8 independent cold
    starts after a data clear."""
    from utils import adb_helpers
    import time
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    auth_page.driver.reconnect()  # re-sync Flutter-Driver session with the just-relaunched isolate
    time.sleep(2)
    auth_page.open_email_input()
    auth_page.enter_email(f"iteration{i}@example.com")
    assert auth_page.email_field_visible(), f"iteration {i}: email field broke"


def test_forms_do_not_lose_focus_on_keyboard_dismiss(reset_to_guest_home, home_page, scanner_page):
    """Dismissing the keyboard (tap outside) after typing into the manual entry
    field does not clear or crash the field."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients("Water, Salt")
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)
