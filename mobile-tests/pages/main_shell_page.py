from .base_page import BasePage


class MainShellPage(BasePage):
    """mobile/lib/shared/widgets/main_shell.dart — bottom navigation bar
    wrapping Home / History / Profile. Classic Material 2
    BottomNavigationBar (single label per tab), NOT the Material 3
    NavigationBar dual-label crossfade — by_key is still used for
    consistency with the rest of the suite, but by_text on the tab
    label would also be unambiguous here, unlike a Material 3 app."""

    NAV_HOME = "nav_home"
    NAV_HISTORY = "nav_history"
    NAV_PROFILE = "nav_profile"
    BOTTOM_NAV = "main_bottom_nav"

    def go_home(self) -> None:
        self.tap_key(self.NAV_HOME)

    def go_history(self) -> None:
        self.tap_key(self.NAV_HISTORY)

    def go_profile(self) -> None:
        self.tap_key(self.NAV_PROFILE)

    def is_visible(self) -> bool:
        return self.is_displayed_by_key(self.BOTTOM_NAV)
