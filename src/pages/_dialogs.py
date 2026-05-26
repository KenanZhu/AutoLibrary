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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages._overlay import Overlay


class SeatMapOverlay(Overlay):
    """
        Seat selection overlay that opens after choosing a floor and room.
    """

    ROOT       = (By.ID, "seatLayout")
    SEAT_ITEMS = (By.CSS_SELECTOR, "li[id^='seat_']")

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        super().__init__(driver, self.ROOT)

    def selectSeat(
        self,
        seat_id: str,
    ) -> str | None:

        try:
            self._waitAllPresence(self.SEAT_ITEMS)
        except (NoSuchElementException, TimeoutException):
            return None
        except Exception:
            return None
        try:
            all_seats = self._findAll(*self.SEAT_ITEMS)
            seat_id_upper = seat_id.lstrip('0').upper()
            for seat in all_seats:
                if not seat_id_upper == seat.text.lstrip('0'):
                    continue
                seat_link = seat.find_element(By.TAG_NAME, "a")
                self._waitClickable((By.TAG_NAME, "a"))
                seat_link.click()
                return seat_link.get_attribute("title")
            return None
        except (NoSuchElementException, TimeoutException,
                ElementNotInteractableException, StaleElementReferenceException):
            return None
        except Exception:
            return None


class TimeSelectDialog(Overlay):
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


class ReserveResultDialog(Overlay):
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
            return self._find(*self._titleLocator()).text
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

    def _titleLocator(
        self,
    ) -> tuple:

        return (By.CSS_SELECTOR, ".layoutSeat dt")


class CheckinResultDialog(Overlay):
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
