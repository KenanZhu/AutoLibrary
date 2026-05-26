# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)

from pages.ReserveView import ReserveView
from pages.RecordsView import RecordsView


class MainShell:

    TAB_RESERVE  = (By.XPATH, "//a[@href='/map']")
    TAB_HISTORY  = (By.XPATH, "//a[@href='/history?type=SEAT']")
    TAB_LOGOUT   = (By.XPATH, "//a[@href='/logout']")

    BTN_CHECKIN  = (By.ID, "btnCheckIn")
    BTN_EXTEND   = (By.ID, "btnExtend")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        self._driver = driver

    def gotoReserveView(
        self,
    ) -> ReserveView:

        self._clickTab(self.TAB_RESERVE)
        WebDriverWait(self._driver, 2).until(
            EC.presence_of_element_located((By.ID, "seatLayout"))
        )
        return ReserveView(self._driver)

    def gotoRecordsView(
        self,
    ) -> RecordsView:

        self._clickTab(self.TAB_HISTORY)
        WebDriverWait(self._driver, 2).until(
            EC.presence_of_element_located((By.CLASS_NAME, "myReserveList"))
        )
        return RecordsView(self._driver)

    def logout(
        self,
    ) -> bool:

        try:
            self._driver.find_element(*self.TAB_LOGOUT).click()
            return True
        except NoSuchElementException:
            return False
        except Exception:
            return False

    def waitCheckinButton(
        self,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(self.BTN_CHECKIN)
            )
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

    def waitExtendButton(
        self,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(self.BTN_EXTEND)
            )
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

    def isCheckinButtonDisabled(
        self,
    ) -> bool:

        btn = self._driver.find_element(*self.BTN_CHECKIN)
        return "disabled" in btn.get_attribute("class")

    def isExtendButtonDisabled(
        self,
    ) -> bool:

        btn = self._driver.find_element(*self.BTN_EXTEND)
        return "disabled" in btn.get_attribute("class")

    def clickCheckinButton(
        self,
    ) -> None:

        btn = WebDriverWait(self._driver, 2).until(
            EC.element_to_be_clickable(self.BTN_CHECKIN)
        )
        btn.click()

    def clickExtendButton(
        self,
    ) -> None:

        btn = WebDriverWait(self._driver, 2).until(
            EC.element_to_be_clickable(self.BTN_EXTEND)
        )
        btn.click()

    def enableCheckinButtonByJS(
        self,
    ) -> bool:

        script = """
        try {
            var checkin_btn = document.getElementById('btnCheckIn');
            if (checkin_btn) {
                checkin_btn.classList.remove('disabled');
                return true;
            }
            return false;
        } catch (e) {
            return false;
        }
        """
        result = self._driver.execute_script(script)
        time.sleep(0.1)
        return result

    def refresh(
        self,
    ) -> None:

        self._driver.refresh()

    def _clickTab(
        self,
        locator: tuple,
    ) -> None:

        WebDriverWait(self._driver, 2).until(
            EC.element_to_be_clickable(locator)
        ).click()
