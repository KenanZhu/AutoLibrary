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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pages.components.Dialog import Dialog


class SeatMapDialog(Dialog):
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
            seat_el = self._find(By.ID, f"seat_{int(seat_id):03d}")
            seat_link = seat_el.find_element(By.TAG_NAME, "a")
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(seat_link)
            )
            seat_link.click()
            return seat_link.get_attribute("title")
        except (NoSuchElementException, ValueError, TimeoutException,
                ElementNotInteractableException, StaleElementReferenceException):
            pass
        except Exception:
            pass
        try:
            all_seats = self._findAll(*self.SEAT_ITEMS)
            seat_id_upper = seat_id.lstrip('0').upper()
            for seat in all_seats:
                if not seat_id_upper == seat.text.lstrip('0'):
                    continue
                seat_link = seat.find_element(By.TAG_NAME, "a")
                WebDriverWait(self._driver, 2).until(
                    EC.element_to_be_clickable(seat_link)
                )
                seat_link.click()
                return seat_link.get_attribute("title")
            return None
        except (NoSuchElementException, TimeoutException,
                ElementNotInteractableException, StaleElementReferenceException):
            return None
        except Exception:
            return None
