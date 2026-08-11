from selenium.webdriver.common.by import By

from pages.base_page import BasePage
import config


class ScanPage(BasePage):
    HEADING = (By.TAG_NAME, "h1")
    BARCODE_INPUT = (By.ID, "input-barcode")
    BARCODE_SUBMIT_BTN = (By.ID, "btn-scan-barcode")
    INGREDIENTS_INPUT = (By.ID, "input-ingredients")
    INGREDIENTS_SUBMIT_BTN = (By.ID, "btn-analyse-ingredients")
    # The tab toggle between "barcode" and "ingredients"
    INGREDIENTS_TAB = (By.ID, "tab-ingredients")
    ERROR_TEXT = (By.XPATH, "//*[contains(@style,'flagged-red') or contains(@class,'error')]")

    def open_scan(self):
        self.open(config.ROUTES["scan"])
        return self

    def heading_text(self, timeout: int = None) -> str:
        return self.wait_visible(*self.HEADING, timeout=timeout).text

    def submit_empty_barcode(self):
        field = self.wait_visible(*self.BARCODE_INPUT)
        field.clear()
        self.click_visible(*self.BARCODE_SUBMIT_BTN)
        return self

    def submit_barcode(self, value: str):
        field = self.wait_visible(*self.BARCODE_INPUT)
        field.clear()
        field.send_keys(value)
        self.click_visible(*self.BARCODE_SUBMIT_BTN)
        return self

    def switch_to_ingredients_tab(self):
        self.click_visible(*self.INGREDIENTS_TAB)
        self.wait_visible(*self.INGREDIENTS_INPUT)
        return self

    def submit_empty_ingredients(self):
        field = self.wait_visible(*self.INGREDIENTS_INPUT)
        field.clear()
        self.click_visible(*self.INGREDIENTS_SUBMIT_BTN)
        return self

    def submit_ingredients(self, text: str):
        field = self.wait_visible(*self.INGREDIENTS_INPUT)
        field.clear()
        field.send_keys(text)
        self.click_visible(*self.INGREDIENTS_SUBMIT_BTN)
        return self

    def has_visible_error(self, timeout: int = None) -> bool:
        t = timeout or config.SHORT_TIMEOUT
        try:
            self.wait_visible(*self.ERROR_TEXT, timeout=t)
            return True
        except Exception:
            return False
