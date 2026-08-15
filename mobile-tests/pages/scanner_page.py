from .base_page import BasePage


class ScannerPage(BasePage):
    """mobile/lib/features/scanner/screens/scanner_screen.dart"""

    BACK_BTN = "scanner_back_btn"
    AR_TOGGLE_BTN = "scanner_ar_toggle_btn"
    FLASH_TOGGLE_BTN = "scanner_flash_toggle_btn"
    TYPE_BTN = "scanner_type_btn"
    CAPTURE_BTN = "scanner_capture_btn"
    GALLERY_BTN = "scanner_gallery_btn"
    MANUAL_TEXT_FIELD = "scanner_manual_text_field"
    MANUAL_SUBMIT_BTN = "scanner_manual_submit_btn"

    def is_loaded(self) -> bool:
        return self.is_on_screen("scanner")

    def go_back(self) -> None:
        self.tap_key(self.BACK_BTN)

    def toggle_ar_overlay(self) -> None:
        self.tap_key(self.AR_TOGGLE_BTN)

    def toggle_flash(self) -> None:
        self.tap_key(self.FLASH_TOGGLE_BTN)

    def open_manual_entry(self) -> None:
        self.tap_key(self.TYPE_BTN)

    def capture_photo(self) -> None:
        self.tap_key(self.CAPTURE_BTN)

    def pick_from_gallery(self) -> None:
        self.tap_key(self.GALLERY_BTN)

    def enter_manual_ingredients(self, text: str) -> None:
        self.enter_text_by_key(self.MANUAL_TEXT_FIELD, text)

    def submit_manual_ingredients(self) -> None:
        self.tap_key(self.MANUAL_SUBMIT_BTN)

    def capture_button_visible(self) -> bool:
        return self.is_displayed_by_key(self.CAPTURE_BTN)
