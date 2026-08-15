from .base_page import BasePage


class HistoryPage(BasePage):
    """mobile/lib/features/history/screens/history_screen.dart

    Row keys are data-driven (history_tile_<id>, history_delete_btn_<id>)
    because the list is backed by the on-device Drift DB, not a fixed
    fixture — tests that need a specific row must scan first (or seed via
    adb_helpers.clear_app_data() for a guaranteed-empty state) rather than
    assuming a row id."""

    LIST = "history_list"
    EMPTY_SCAN_NOW_BTN = "history_empty_scan_now_btn"

    def is_loaded(self) -> bool:
        return self.is_on_screen("history")

    def is_empty_state_visible(self) -> bool:
        return self.is_displayed_by_key(self.EMPTY_SCAN_NOW_BTN)

    def is_list_visible(self) -> bool:
        return self.is_displayed_by_key(self.LIST)

    def tap_empty_state_scan_now(self) -> None:
        self.tap_key(self.EMPTY_SCAN_NOW_BTN)

    def tap_row(self, scan_id: str) -> None:
        self.tap_key(f"history_tile_{scan_id}")

    def delete_row(self, scan_id: str) -> None:
        self.tap_key(f"history_delete_btn_{scan_id}")
