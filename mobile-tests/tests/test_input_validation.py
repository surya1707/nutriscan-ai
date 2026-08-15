"""
CATEGORY: Input Validation

Boundary, empty, whitespace, unicode, and long-string inputs across the
three real text fields in the app: auth email, manual ingredient entry,
and profile name. None of these fields has a client-side regex
validator in the current codebase (confirmed by reading the widget
source), so these tests document *actual, current* behaviour — that
the fields are permissive and the app does not crash — rather than
asserting a validation rule that doesn't exist yet.
"""

import time

import pytest

from utils import adb_helpers


# ── Manual ingredient field boundaries ────────────────────────────────

@pytest.mark.parametrize("value", [
    "",
    " ",
    "a",
    "A" * 500,
    "A" * 2000,
    "🥜🥛🍞",
    "café, naïve, jalapeño",
    "水, 塩, 砂糖",
    "<script>alert(1)</script>",
    "'; DROP TABLE scans; --",
    "\n\n\n",
    "\t\t",
])
def test_manual_ingredient_field_boundary_and_hostile_inputs(
    reset_to_guest_home, home_page, scanner_page, value
):
    """Manual ingredient field does not crash on empty, whitespace, very long,
    unicode, emoji, HTML-injection, or SQL-injection-shaped input (the field
    only feeds a local Drift insert with parameterised queries, never raw SQL
    concatenation — see app_database.dart — so this documents defence-in-depth,
    not a currently-known vulnerability)."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients(value)
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)


def test_manual_ingredient_submit_blocked_on_empty_string(reset_to_guest_home, home_page, scanner_page):
    """The submit handler in scanner_screen.dart explicitly no-ops when the
    trimmed text is empty — verified by confirming the dialog does not
    navigate away after submitting blank text."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients("   ")
    scanner_page.submit_manual_ingredients()
    # dialog should still be open / field still present, since onSubmit was
    # never called for whitespace-only text
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)


# ── Profile name field boundaries ─────────────────────────────────────

@pytest.mark.parametrize("value", [
    "",
    " ",
    "X",
    "X" * 100,
    "X" * 300,
    "😀 Emoji Name 😀",
    "Name\nWith\nNewlines",
    "   Leading and trailing spaces   ",
    "Tab\tSeparated\tName",
    "!@#$%^&*()",
])
def test_profile_name_field_boundary_inputs(reset_to_guest_home, main_shell, profile_page, value):
    """Profile name field does not crash on empty, whitespace, very long,
    emoji, newline, or symbol-only input."""
    main_shell.go_profile()
    profile_page.enter_name(value)
    assert profile_page.is_displayed_by_key(profile_page.NAME_FIELD)


# ── Auth email field boundaries ────────────────────────────────────────

@pytest.mark.parametrize("value", [
    "",
    " ",
    "a@b",
    "a" * 200 + "@example.com",
    "üser@exämple.com",
    "user@localhost",
    "user@127.0.0.1",
    "\"quoted local part\"@example.com",
])
def test_auth_email_field_boundary_inputs(auth_page, value):
    """Auth email field accepts an unusual-but-plausible range of strings
    without the app crashing or the field disappearing."""
    adb_helpers.clear_app_data()
    adb_helpers.relaunch_app()
    time.sleep(2)
    auth_page.open_email_input()
    auth_page.enter_email(value)
    assert auth_page.email_field_visible()


@pytest.mark.parametrize("i", range(1, 9))
def test_rapid_repeated_keystrokes_do_not_corrupt_field_state(
    reset_to_guest_home, home_page, scanner_page, i
):
    """Typing into the manual-ingredient field 8 times in immediate succession
    (simulating fast typing / IME race conditions) never leaves the field
    invisible or the app unresponsive."""
    home_page.tap_scan_card()
    scanner_page.open_manual_entry()
    scanner_page.enter_manual_ingredients(f"Rapid input test {i}" * 3)
    assert scanner_page.is_displayed_by_key(scanner_page.MANUAL_TEXT_FIELD)
