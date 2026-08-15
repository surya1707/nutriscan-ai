from .base_page import BasePage


class ProfilePage(BasePage):
    """mobile/lib/features/profile/screens/profile_screen.dart

    Allergy / condition / goal chips act as the app's only filter-style
    UI (there is no search/filter bar anywhere in the app — see
    mobile-tests/README.md "Coverage honesty note"). Each chip has its
    own ValueKey: profile_chip_<group>_<item>."""

    NAME_FIELD = "profile_name_field"
    SAVE_BTN = "profile_save_btn"
    SIGN_OUT_BTN = "profile_sign_out_btn"

    def is_loaded(self) -> bool:
        return self.is_on_screen("profile")

    def enter_name(self, name: str) -> None:
        self.enter_text_by_key(self.NAME_FIELD, name)

    def save(self) -> None:
        self.tap_key(self.SAVE_BTN)

    def sign_out(self) -> None:
        self.tap_key(self.SIGN_OUT_BTN)

    def chip_key(self, group: str, item: str) -> str:
        return f"profile_chip_{group}_{item}"

    def toggle_chip(self, group: str, item: str) -> None:
        self.tap_key(self.chip_key(group, item))

    def chip_visible(self, group: str, item: str) -> bool:
        return self.is_displayed_by_key(self.chip_key(group, item))

    def save_btn_visible(self) -> bool:
        return self.is_displayed_by_key(self.SAVE_BTN)
