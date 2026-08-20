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

    # Chip groups stack vertically inside profile_screen.dart's
    # SingleChildScrollView in this order: allergies, conditions, goals.
    # "Allergies" (the first group) starts within the viewport at scroll
    # position 0, but "conditions" and "goals" render below the fold.
    # appium-flutter-driver's flutter:clickElement taps the widget's actual
    # on-screen render coordinates (like WidgetController.tap) rather than
    # scrolling it into view first (unlike Espresso's scrollTo()) — a tap
    # on a chip that is scrolled off-screen lands outside the viewport and
    # is silently swallowed. Scrolling down first (same adb-swipe mechanism
    # already used elsewhere for the equivalent-unsupported
    # "mobile: scrollGesture" command) puts the target group in view before
    # every tap on a non-"allergies" chip.
    _GROUP_SWIPES = {"conditions": 1, "goals": 2}

    def chip_key(self, group: str, item: str) -> str:
        return f"profile_chip_{group}_{item}"

    def toggle_chip(self, group: str, item: str) -> None:
        for _ in range(self._GROUP_SWIPES.get(group, 0)):
            self.swipe_up()
        self.tap_key(self.chip_key(group, item))

    def chip_visible(self, group: str, item: str) -> bool:
        return self.is_displayed_by_key(self.chip_key(group, item))

    def save_btn_visible(self) -> bool:
        return self.is_displayed_by_key(self.SAVE_BTN)
