from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.parsers.base_parser import BaseParser
from backend.parsers.browser_utils import get_chrome_options
from backend.parsers.price_utils import clean_price


class MVideoParser(BaseParser):
    def parse_price(self, url: str) -> float:
        options = get_chrome_options()

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)

            selectors = [
                ".price__main-value",
            ]

            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 1).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, selector)
                        )
                    )

                    price_text = element.get_attribute("content") or element.text

                    if price_text:
                        return clean_price(price_text)

                except TimeoutException:
                    continue

            raise ValueError("Цена на странице М.Видео не найдена")

        finally:
            driver.quit()