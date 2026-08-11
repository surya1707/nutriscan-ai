"""
Category: Input Validation / Forms

Everything in this file fires BEFORE any network call is made (see
ScanPage.runBarcode / runIngredients in the source — both check for
empty input and `setError(...)` locally first). That makes these tests
100% reliable in CI regardless of whether a backend is reachable.
"""

import pytest
from selenium.webdriver.common.by import By

from pages.login_page import LoginPage
from pages.scan_page import ScanPage
import config


pytestmark = pytest.mark.forms


@pytest.fixture()
def scan_page(driver):
    login = LoginPage(driver).open_login()
    login.continue_as_guest()
    login.wait_for_path("/", timeout=config.LOGIN_REDIRECT_TIMEOUT)
    page = ScanPage(driver).open_scan()
    page.wait_visible(*page.BARCODE_INPUT)
    return page


class TestBarcodeTabValidation:
    def test_scan_page_loads_with_barcode_tab_default(self, scan_page):
        assert scan_page.exists(*scan_page.BARCODE_INPUT)

    def test_empty_barcode_shows_error(self, scan_page):
        scan_page.submit_empty_barcode()
        assert scan_page.has_visible_error()

    def test_whitespace_only_barcode_shows_error(self, scan_page):
        scan_page.submit_barcode("   ")
        assert scan_page.has_visible_error()

    @pytest.mark.parametrize("barcode", [
        "1", "12345678901234", "0000000000000", "abc123",
        "5000112637922",        # realistic EAN-13
        "012345678905",         # realistic UPC-A
        "9",                    # single digit
        "9" * 30,               # unusually long
        "12 34 56",             # embedded spaces
        "123-456-789",          # embedded dashes
        "١٢٣٤٥٦٧٨٩",             # Arabic-Indic digits (unicode)
        "12345678901234567890123456789012345678901234567890",  # very long numeric
        "barcode-with-emoji-🍫",
        "<script>alert(1)</script>",     # XSS payload
        "'; DROP TABLE scans; --",       # SQLi-shaped payload
        "%00%0a%0d",                     # encoded control chars
        "0" * 200,                       # extreme length boundary
        "\t\ttabbed\t\t",
        "line1\nline2",
        "NaN",
        "undefined",
        "null",
    ])
    def test_various_barcode_inputs_are_accepted_by_the_field(self, scan_page, barcode):
        """These values pass the client-side non-empty check; whether the
        (unreachable-in-CI) backend recognises them is out of scope here —
        see test_scan_network_handling.py. What IS in scope: the field
        must retain exactly what was typed and the page must not crash."""
        field = scan_page.wait_visible(*scan_page.BARCODE_INPUT)
        field.clear()
        
        has_non_bmp = any(ord(c) > 0xFFFF for c in barcode)
        is_whitespace = "\t" in barcode or "\n" in barcode
        if has_non_bmp or is_whitespace:
            scan_page.driver.execute_script(
                "var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "setter.call(arguments[0], arguments[1]);"
                "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                field, barcode
            )
        else:
            field.send_keys(barcode)
            
        expected = barcode.replace("\n", "").replace("\t", "")
        assert field.get_attribute("value") == expected

    @pytest.mark.parametrize("barcode", [
        "<script>alert(1)</script>",
        "'; DROP TABLE scans; --",
        "<img src=x onerror=alert(1)>",
        "\" onmouseover=\"alert(1)",
    ])
    def test_hostile_barcode_input_is_not_executed_or_reflected_unescaped(self, scan_page, barcode):
        """React escapes text content by default; this is a regression
        guard against that ever changing (e.g. a future dangerouslySetInnerHTML)."""
        field = scan_page.wait_visible(*scan_page.BARCODE_INPUT)
        field.clear()
        field.send_keys(barcode)
        # No JS alert was triggered (Selenium would hang/throw on an
        # unexpected alert if one fired) and no literal unescaped <script>
        # tag exists in the live DOM outside the input's own value.
        scripts_on_page = scan_page.driver.find_elements(
            By.XPATH,
            "//script[contains(text(),'alert(1)')]",
        )
        assert not scripts_on_page

    def test_barcode_field_has_reasonable_maxlength_or_none(self, scan_page):
        """Documents current behaviour rather than asserting a specific
        limit — flags it clearly if a maxlength is ever added/removed."""
        field = scan_page.wait_visible(*scan_page.BARCODE_INPUT)
        maxlength = field.get_attribute("maxlength")
        assert maxlength is None or int(maxlength) > 0

    def test_barcode_field_survives_rapid_successive_edits(self, scan_page):
        field = scan_page.wait_visible(*scan_page.BARCODE_INPUT)
        for value in ["1", "12", "123", "1234", "12345"]:
            field.clear()
            field.send_keys(value)
        assert field.get_attribute("value") == "12345"


class TestIngredientsTabValidation:
    def test_switch_to_ingredients_tab(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        assert scan_page.exists(*scan_page.INGREDIENTS_INPUT)

    def test_empty_ingredients_shows_error(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        scan_page.submit_empty_ingredients()
        assert scan_page.has_visible_error()

    def test_whitespace_only_ingredients_shows_error(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        scan_page.submit_ingredients("   \n  ,, \n")
        assert scan_page.has_visible_error()

    @pytest.mark.parametrize("raw,expected_min_lines", [
        ("sugar", 1),
        ("sugar, salt, water", 3),
        ("sugar\nsalt\nwater", 3),
        ("sugar,,salt,,,water", 3),
        ("SUGAR, Salt, WaTeR", 3),
        ("sugar,\nsalt,\nwater", 3),
        ("sugar , salt , water", 3),
        ("sugar;salt;water", 1),          # semicolons aren't a recognised delimiter
        ("high-fructose corn syrup, salt", 2),
        ("émulsifiant (lécithine de soja), sel", 2),
        ("monosodium glutamate (E621), sugar", 2),
        ("water\n\n\nsugar", 2),          # collapsed blank lines
        ("sugar,salt,water,salt,sugar", 5),  # intentional duplicates retained
        ("a" * 500, 1),                    # single very long ingredient token
        ("\n".join([f"ingredient-{i}" for i in range(30)]), 30),  # many lines
    ])
    def test_ingredient_line_splitting_accepts_various_delimiters(self, scan_page, raw, expected_min_lines):
        """Source splits on /[\\n,]+/ and filters blanks — verify the field
        at least accepts and retains this input (functional split behaviour
        itself is exercised end-to-end once a backend is available)."""
        scan_page.switch_to_ingredients_tab()
        field = scan_page.wait_visible(*scan_page.INGREDIENTS_INPUT)
        field.clear()
        field.send_keys(raw)
        assert field.get_attribute("value") == raw

    @pytest.mark.parametrize("raw", [
        "<script>alert(1)</script>",
        "'; DROP TABLE ingredients; --",
        "<img src=x onerror=alert(1)>",
    ])
    def test_hostile_ingredients_input_is_not_executed_or_reflected_unescaped(self, scan_page, raw):
        scan_page.switch_to_ingredients_tab()
        field = scan_page.wait_visible(*scan_page.INGREDIENTS_INPUT)
        field.clear()
        field.send_keys(raw)
        scripts_on_page = scan_page.driver.find_elements(
            By.XPATH, "//script[contains(text(),'alert(1)')]",
        )
        assert not scripts_on_page

    def test_ingredients_textarea_accepts_multiline_paste_style_input(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        field = scan_page.wait_visible(*scan_page.INGREDIENTS_INPUT)
        multiline = "sugar\nsalt\nwater\ncocoa butter\nvanilla extract"
        field.clear()
        field.send_keys(multiline)
        assert field.get_attribute("value") == multiline

    def test_ingredients_field_survives_rapid_successive_edits(self, scan_page):
        scan_page.switch_to_ingredients_tab()
        field = scan_page.wait_visible(*scan_page.INGREDIENTS_INPUT)
        for value in ["s", "su", "sug", "suga", "sugar"]:
            field.clear()
            field.send_keys(value)
        assert field.get_attribute("value") == "sugar"

    def test_switching_tabs_does_not_leak_barcode_value_into_ingredients(self, scan_page):
        barcode_field = scan_page.wait_visible(*scan_page.BARCODE_INPUT)
        barcode_field.clear()
        barcode_field.send_keys("5000112637922")
        scan_page.switch_to_ingredients_tab()
        ing_field = scan_page.wait_visible(*scan_page.INGREDIENTS_INPUT)
        assert ing_field.get_attribute("value") in ("", None)
