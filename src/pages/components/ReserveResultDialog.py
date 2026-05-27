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
    StaleElementReferenceException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.components.Dialog import Dialog


class ReserveResultDialog(Dialog):
    """
        Reservation result dialog shown after submitting a reserve request.
    """

    ROOT = (By.CLASS_NAME, "layoutSeat")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        super().__init__(driver, self.ROOT, auto_close_on_exit=False)

    def getTitle(
        self,
    ) -> str:

        try:
            return self._find(*self._title_locator()).text
        except (NoSuchElementException, StaleElementReferenceException):
            return ""
        except Exception:
            return ""

    def isSuccess(
        self,
    ) -> bool:

        title = self.getTitle()
        return any(
            kw in title
            for kw in ("预定好了", "预约成功", "操作成功")
        )

    def isFailure(
        self,
    ) -> bool:

        contents = self.getDetailTexts()
        return any(
            "预约失败" in msg or "已有1个有效预约" in msg
            for msg in contents
        )

    def getDetailTexts(
        self,
    ) -> list[str]:

        try:
            elements = self._findAll(By.CSS_SELECTOR, ".layoutSeat dd")
            return [el.text for el in elements if el.text.strip()]
        except (NoSuchElementException, StaleElementReferenceException):
            return []
        except Exception:
            return []

    def _title_locator(
        self,
    ) -> tuple:

        return (By.CSS_SELECTOR, ".layoutSeat dt")
