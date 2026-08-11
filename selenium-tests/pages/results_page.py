from selenium.webdriver.common.by import By

from pages.base_page import BasePage
import config


class ResultsPage(BasePage):
    HEADING = (By.XPATH, "//h1[contains(text(),'Scan Results')]")
    BACK_BTN = (By.ID, "btn-results-back")
    SCAN_ANOTHER_BTN = (By.ID, "btn-scan-another")

    def open_results(self, scan_id: str = "new"):
        self.open(f"results/{scan_id}")
        return self

    def go_back(self):
        self.click_visible(*self.BACK_BTN)
        return self
