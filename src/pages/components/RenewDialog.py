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
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from pages.components.Overlay import Overlay


class RenewDialog(Overlay):
    """
        Renewal time selection dialog.
    """

    ROOT = (By.ID, "extendDiv")

    MESSAGE_HEAD = (By.CSS_SELECTOR, "#extendDiv p.messageHead")
    RESULT_MSG   = (By.CSS_SELECTOR, "#extendDiv div.resultMessage")
    TIME_OPTS    = (By.CSS_SELECTOR, "#extendDiv .renewal_List li")
    OK_BTN       = (By.CSS_SELECTOR, "#extendDiv .btnOK")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        super().__init__(driver, self.ROOT, auto_close_on_exit=False)

    def waitUntilReady(
        self,
    ) -> bool:

        try:
            self._waitVisible(self.ROOT)
            self._waitPresence(self.MESSAGE_HEAD)
            self._waitPresence(self.RESULT_MSG)
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception:
            return False
        head_msg = self._find(*self.MESSAGE_HEAD).text.strip()
        if "警告" in head_msg:
            return False
        try:
            self._waitAllPresence(self.TIME_OPTS)
            self._waitPresence(self.OK_BTN)
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception:
            return False
        return True

    def getHeadMessage(
        self,
    ) -> str:

        return self._find(*self.MESSAGE_HEAD).text.strip()

    def getResultMessage(
        self,
    ) -> str:

        return self._find(*self.RESULT_MSG).text.strip()

    def getTimeOptions(
        self,
    ) -> list[WebElement]:

        return self._findAll(*self.TIME_OPTS)

    def getOkButton(
        self,
    ) -> WebElement:

        return self._find(*self.OK_BTN)

    def clickOk(
        self,
    ) -> bool:

        try:
            self._find(*self.OK_BTN).click()
            return True
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
            return False
        except Exception:
            return False
