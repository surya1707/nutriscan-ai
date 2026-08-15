from .base_page import BasePage


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
        self.wait_for_text("Eat with", timeout=15)  # home screen headline

    def email_field_visible(self) -> bool:
        return self.is_displayed_by_key(self.EMAIL_FIELD)
