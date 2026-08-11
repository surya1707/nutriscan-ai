from selenium.webdriver.common.by import By

from pages.base_page import BasePage
import config


class LoginPage(BasePage):
    GOOGLE_BTN = (By.ID, "btn-google-signin")
    EMAIL_TOGGLE_BTN = (By.ID, "btn-email-signin")
    EMAIL_INPUT = (By.ID, "input-email")
    EMAIL_SEND_BTN = (By.ID, "btn-email-send")
    GUEST_BTN = (By.ID, "btn-guest")
    ERROR_BANNER = (By.XPATH, "//*[contains(text(), 'valid email') or contains(text(), 'failed') or contains(text(), 'Failed')]")
    EMAIL_SENT_CONFIRMATION = (By.XPATH, "//*[contains(text(), 'Sign-in link sent')]")
    HEADING = (By.TAG_NAME, "h1")

    def open_login(self):
        self.open(config.ROUTES["login"])
        self.wait_visible(*self.GOOGLE_BTN)
        return self

    def heading_text(self) -> str:
        return self.wait_visible(*self.HEADING).text

    def click_google(self):
        self.click_visible(*self.GOOGLE_BTN)
        return self

    def reveal_email_form(self):
        self.click_visible(*self.EMAIL_TOGGLE_BTN)
        self.wait_visible(*self.EMAIL_INPUT)
        return self

    def submit_email(self, email: str):
        field = self.wait_visible(*self.EMAIL_INPUT)
        field.clear()
        field.send_keys(email)
        self.click_visible(*self.EMAIL_SEND_BTN)
        return self

    def continue_as_guest(self):
        self.click_visible(*self.GUEST_BTN)
        return self

    def has_error_banner(self, timeout: int = None) -> bool:
        t = timeout or config.SHORT_TIMEOUT
        try:
            self.wait_visible(*self.ERROR_BANNER, timeout=t)
            return True
        except Exception:
            return False

    def has_email_sent_confirmation(self, timeout: int = None) -> bool:
        t = timeout or config.SHORT_TIMEOUT
        try:
            self.wait_visible(*self.EMAIL_SENT_CONFIRMATION, timeout=t)
            return True
        except Exception:
            return False
