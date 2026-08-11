from selenium.webdriver.common.by import By

from pages.base_page import BasePage
import config


class HomePage(BasePage):
    HEADING = (By.TAG_NAME, "h1")

    def open_home(self):
        self.open(config.ROUTES["home"])
        return self

    def heading_text(self, timeout: int = None) -> str:
        return self.wait_visible(*self.HEADING, timeout=timeout).text
