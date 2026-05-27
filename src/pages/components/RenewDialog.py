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
from selenium.webdriver.remote.webelement import WebElement

from pages.components.Dialog import Dialog
from pages.strategies.TimeSelectMaker import (
    TimeSelectionResult,
    TimeSelectMaker,
)


class RenewDialog(Dialog):
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
        except TimeoutException:
            return False
        head_msg = self._find(*self.MESSAGE_HEAD).text.strip()
        if "警告" in head_msg:
            return False
        try:
            self._waitAllPresence(self.TIME_OPTS)
            self._waitPresence(self.OK_BTN)
        except TimeoutException:
            return False
        return True

    def getHeadMessage(
        self,
    ) -> str:

        try:
            return self._find(*self.MESSAGE_HEAD).text.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            return ""

    def getResultMessage(
        self,
    ) -> str:

        try:
            return self._find(*self.RESULT_MSG).text.strip()
        except (NoSuchElementException, StaleElementReferenceException):
            return ""

    def getTimeOptions(
        self,
    ) -> list[WebElement]:

        return self._findAll(*self.TIME_OPTS)

    def selectBestTime(
        self,
        target_time: int,
        max_time_diff: int,
        prefer_earlier: bool,
    ) -> TimeSelectionResult:

        all_time_opts = self.getTimeOptions()
        if not all_time_opts:
            return TimeSelectionResult()
        result = TimeSelectMaker.forRenew().decide(
            all_time_opts,
            target_time,
            max_time_diff,
            prefer_earlier,
        )
        if result.selected_index >= 0:
            try:
                all_time_opts[result.selected_index].click()
            except (ElementNotInteractableException, StaleElementReferenceException):
                return TimeSelectionResult(free_times=result.free_times)
        return result

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
        except (NoSuchElementException, ElementNotInteractableException):
            return False
