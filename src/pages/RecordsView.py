# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)


class RecordsView:

    RECORDS_LIST = (By.CSS_SELECTOR, ".myReserveList > dl:not(#moreBlock)")
    MORE_BTN     = (By.ID, "more_btn")
    RECORD_TIME  = (By.CSS_SELECTOR, "dt")
    RECORD_INFO  = (By.CSS_SELECTOR, "a")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        self._driver = driver

    def loadRecords(
        self,
    ) -> list | None:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.RECORDS_LIST)
            )
            return self._driver.find_elements(*self.RECORDS_LIST)
        except TimeoutException:
            return None
        except Exception:
            return None

    def getRecordTimeElement(
        self,
        record: WebElement,
    ) -> WebElement:

        return record.find_element(*self.RECORD_TIME)

    def getRecordInfoElements(
        self,
        record: WebElement,
    ) -> list[WebElement]:

        return record.find_elements(*self.RECORD_INFO)

    def showMoreRecords(
        self,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(self.MORE_BTN)
            )
        except TimeoutException:
            return False
        except Exception:
            return False
        try:
            more_btn = self._driver.find_element(*self.MORE_BTN)
            if more_btn.is_displayed() and more_btn.is_enabled():
                self._driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                self._driver.execute_script("arguments[0].click();", more_btn)
                return True
            return False
        except (NoSuchElementException, StaleElementReferenceException):
            return False
        except Exception:
            return False

    def getRecordText(
        self,
        record: WebElement,
    ) -> str:

        return record.text.strip()
