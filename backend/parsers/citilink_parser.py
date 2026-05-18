from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.parsers.base_parser import BaseParser
from backend.parsers.browser_utils import get_chrome_options
from backend.parsers.price_utils import clean_price


class CitilinkParser(BaseParser):
    def parse_price(self, url: str) -> float:
        options = get_chrome_options()

        driver = webdriver.Chrome(options=options)

        try:
            driver.get(url)

            selectors = [
                "[data-meta-price]",
            ]

            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 1).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, selector)
                        )
                    )

                    price_text = (
                        element.get_attribute("data-meta-price")
                        or element.text
                    )

                    if price_text:
                        return clean_price(price_text)

                except TimeoutException:
                    continue

            raise ValueError("Цена на странице Ситилинка не найдена")

        finally:
            driver.quit()