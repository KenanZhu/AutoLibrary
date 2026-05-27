# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from pages.components.Dialog import Dialog


class TimeSelectDialog(Dialog):
    """
        Time selection panel that appears after selecting a seat.

        Contains start-time and end-time option lists.
        Does NOT auto-close — the reserve submission handles cleanup.
    """

    ROOT = (By.CSS_SELECTOR, "#startTime ul")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        super().__init__(driver, self.ROOT, auto_close_on_exit=False)

    def getTimeOptions(
        self,
        time_id: str,
    ) -> list[WebElement]:

        try:
            self._waitAllPresence(
                (By.CSS_SELECTOR, f"#{time_id} ul li a")
            )
        except (NoSuchElementException, TimeoutException):
            return []
        except Exception:
            return []
        return self._findAll(
            By.CSS_SELECTOR,
            f"#{time_id} ul li a",
        )
