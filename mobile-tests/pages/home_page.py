from .base_page import BasePage


class HomePage(BasePage):
    """mobile/lib/features/home/screens/home_screen.dart"""

    SCAN_CARD = "home_scan_card"
    PERSONALIZE_BANNER = "home_personalize_banner"

    def is_loaded(self, timeout: int = None) -> bool:
        return self.is_on_screen("home", timeout)

    def tap_scan_card(self) -> None:
        self.tap_key(self.SCAN_CARD)

    def tap_personalize_banner(self) -> None:
        self.tap_key(self.PERSONALIZE_BANNER)

    def scan_card_visible(self) -> bool:
        return self.is_displayed_by_key(self.SCAN_CARD)

    def greeting_shows_guest(self) -> bool:
        return self.wait_for_text("Guest", timeout=5)
