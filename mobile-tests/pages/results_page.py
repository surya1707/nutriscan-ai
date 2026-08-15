from .base_page import BasePage


class ResultsPage(BasePage):
    """mobile/lib/features/scanner/screens/results_screen.dart"""

    BACK_BTN = "results_back_btn"
    SHARE_BTN = "results_share_btn"

    def is_loaded(self) -> bool:
        return self.is_on_screen("results")

    def go_back(self) -> None:
        self.tap_key(self.BACK_BTN)

    def tap_share(self) -> None:
        self.tap_key(self.SHARE_BTN)

    def is_visible(self) -> bool:
        return self.is_displayed_by_key(self.BACK_BTN)
