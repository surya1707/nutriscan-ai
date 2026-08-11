from selenium.webdriver.common.by import By

from pages.base_page import BasePage
import config


class HistoryPage(BasePage):
    HEADING = (By.TAG_NAME, "h1")
    LOAD_MORE_BTN = (By.ID, "btn-load-more")
    SKELETON = (By.XPATH, "//*[contains(@style,'pulse')]")

    def open_history(self):
        self.open(config.ROUTES["history"])
        return self

    def heading_text(self, timeout: int = None) -> str:
        return self.wait_visible(*self.HEADING, timeout=timeout).text

    def is_loading(self) -> bool:
        return len(self.find_all_visible(*self.SKELETON)) > 0
