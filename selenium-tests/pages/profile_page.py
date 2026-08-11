from selenium.webdriver.common.by import By

from pages.base_page import BasePage
import config


class ProfilePage(BasePage):
    HEADING = (By.TAG_NAME, "h1")
    SIGNOUT_BTN = (By.ID, "btn-signout-profile")
    DISPLAY_NAME_INPUT = (By.ID, "input-display-name")
    SAVE_BTN = (By.ID, "btn-save-profile")

    def open_profile(self):
        self.open(config.ROUTES["profile"])
        return self

    def heading_text(self, timeout: int = None) -> str:
        return self.wait_visible(*self.HEADING, timeout=timeout).text

    def sign_out(self):
        self.click_visible(*self.SIGNOUT_BTN)
        return self

    def set_display_name(self, value: str):
        field = self.wait_visible(*self.DISPLAY_NAME_INPUT)
        field.clear()
        field.send_keys(value)
        return self

    def save(self):
        self.click_visible(*self.SAVE_BTN)
        return self
