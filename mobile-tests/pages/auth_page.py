from .base_page import BasePage
import config


class AuthPage(BasePage):
    """mobile/lib/features/auth/screens/auth_screen.dart"""

    GOOGLE_BTN = "auth_google_btn"
    EMAIL_TOGGLE_BTN = "auth_email_toggle_btn"
    EMAIL_FIELD = "auth_email_field"
    EMAIL_SEND_BTN = "auth_email_send_btn"
    GUEST_BTN = "auth_guest_btn"

    def is_loaded(self) -> bool:
        return self.is_on_screen("auth")

    def tap_google(self) -> None:
        self.tap_key(self.GOOGLE_BTN)

    def open_email_input(self) -> None:
        self.tap_key(self.EMAIL_TOGGLE_BTN)

    def enter_email(self, email: str) -> None:
        self.enter_text_by_key(self.EMAIL_FIELD, email)

    def submit_email(self) -> None:
        self.tap_key(self.EMAIL_SEND_BTN)

    def continue_as_guest(self) -> None:
        self.tap_key(self.GUEST_BTN)
        # BUG FIX: this previously waited for the literal string "Eat
        # with", but home_screen.dart's headline is a single Text widget
        # whose exact content is 'Eat with\nintelligence.'. Flutter's
        # find.text() does an EXACT match (not substring/prefix), so the
        # old wait could never succeed — it silently burned its full
        # timeout on every single guest login (wait_for_text returns
        # False rather than raising, and every caller here ignores the
        # result) instead of confirming Home actually loaded. Reusing
        # config.ROUTE_TEXT_MARKERS["home"] keeps this in sync with the
        # same marker base_page.is_on_screen("home") already uses,
        # instead of a second, drifting copy of the string.
        self.wait_for_text(config.ROUTE_TEXT_MARKERS["home"], timeout=15)

    def email_field_visible(self) -> bool:
        return self.is_displayed_by_key(self.EMAIL_FIELD)