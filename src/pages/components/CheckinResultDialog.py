# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.components.Dialog import Dialog


class CheckinResultDialog(Dialog):
    """
        Check-in result dialog.
    """

    ROOT = (By.CLASS_NAME, "ui_dialog")

    RESULT_MSG = (By.CLASS_NAME, "resultMessage")
    OK_BTN     = (By.CLASS_NAME, "btnOK")
    DETAIL_DD  = (By.CSS_SELECTOR, ".resultMessage dd")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        super().__init__(driver, self.ROOT, auto_close_on_exit=False)

    def getResultMessage(
        self,
    ) -> str:

        try:
            self._waitPresence(self.RESULT_MSG)
            el = self._find(*self.RESULT_MSG)
            return el.text
        except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
            return ""
        except Exception:
            return ""

    def getDetails(
        self,
    ) -> list[str]:

        try:
            elements = self._findAll(*self.DETAIL_DD)
            return [el.text for el in elements if el.text.strip()]
        except (NoSuchElementException, StaleElementReferenceException):
            return []
        except Exception:
            return []

    def clickOk(
        self,
    ) -> bool:

        try:
            self._waitClickable(self.OK_BTN).click()
            return True
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
            return False
        except Exception:
            return False
