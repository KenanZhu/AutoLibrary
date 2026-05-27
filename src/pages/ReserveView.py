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
    ElementNotInteractableException,
    TimeoutException,
)

from pages.components.SeatMapDialog import SeatMapDialog


class ReserveView:

    DATE_SELECT     = (By.ID, "onDate_select")
    DATE_OPTION_FMT = "p#options_onDate a[value='{value}']"
    DATE_XPATH_FMT  = "//p[@id='options_onDate']/a[@value='{value}']"

    PLACE_SELECT     = (By.ID, "display_building")
    PLACE_OPTION_FMT = "p#options_building a[value='{value}']"
    PLACE_XPATH_FMT  = "//p[@id='options_building']/a[@value='{value}']"

    FLOOR_SELECT     = (By.ID, "floor_select")
    FLOOR_OPTION_FMT = "p#options_floor a[value='{value}']"
    FLOOR_XPATH_FMT  = "//p[@id='options_floor']/a[@value='{value}']"

    FIND_ROOM_BTN = (By.ID, "findRoom")
    ROOM_BTN_FMT  = "room_{room}"

    RESERVE_BTN    = (By.ID, "reserveBtn")

    FLOOR_MAP = {"2": "二层", "3": "三层", "4": "四层", "5": "五层"}
    ROOM_MAP = {
        "1": "二层内环", "2": "二层西区", "3": "三层内环", "4": "三层外环",
        "5": "四层内环", "6": "四层外环", "7": "四层期刊", "8": "五层考研",
    }

    def __init__(
        self,
        driver: WebDriver,
    ) -> None:

        self._driver = driver

    def selectDate(
        self,
        date_str: str,
    ) -> bool:

        if self._clickOptionByJS(
            trigger_id="onDate_select",
            option_css=self.DATE_OPTION_FMT.format(value=date_str),
        ):
            return True
        return self._clickOption(
            trigger=self.DATE_SELECT,
            option=(By.XPATH, self.DATE_XPATH_FMT.format(value=date_str)),
        )

    def selectPlace(
        self,
        place: str = "1",
    ) -> bool:

        if self._clickOptionByJS(
            trigger_id="display_building",
            option_css=self.PLACE_OPTION_FMT.format(value=place),
        ):
            return True
        return self._clickOption(
            trigger=self.PLACE_SELECT,
            option=(By.XPATH, self.PLACE_XPATH_FMT.format(value=place)),
        )

    def selectFloor(
        self,
        floor: str,
    ) -> bool:

        if self._clickOptionByJS(
            trigger_id="floor_select",
            option_css=self.FLOOR_OPTION_FMT.format(value=floor),
        ):
            return True
        return self._clickOption(
            trigger=self.FLOOR_SELECT,
            option=(By.XPATH, self.FLOOR_XPATH_FMT.format(value=floor)),
        )

    def selectRoom(
        self,
        room: str,
    ) -> SeatMapDialog | None:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(self.FIND_ROOM_BTN)
            ).click()
        except (TimeoutException, ElementNotInteractableException):
            return None
        except Exception:
            return None
        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable((By.ID, self.ROOM_BTN_FMT.format(room=room)))
            ).click()
        except (TimeoutException, ElementNotInteractableException):
            return None
        except Exception:
            return None
        try:
            return SeatMapDialog(self._driver)
        except (TimeoutException):
            return None
        except Exception:
            return None

    def submitReserve(
        self,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(self.RESERVE_BTN)
            ).click()
            return True
        except (TimeoutException, ElementNotInteractableException):
            return False
        except Exception:
            return False

    def refresh(
        self,
    ) -> None:

        self._driver.refresh()

    def _clickOptionByJS(
        self,
        trigger_id: str,
        option_css: str,
    ) -> bool:

        script = f"""
        try {{
            var trigger = document.getElementById('{trigger_id}');
            if (trigger) {{
                trigger.click();
                var option = document.querySelector("{option_css}");
                if (option) {{
                    option.click();
                    return true;
                }}
                return false;
            }}
            return false;
        }} catch (e) {{
            return false;
        }}
        """
        result = self._driver.execute_script(script)
        time.sleep(0.1)
        return result

    def _clickOption(
        self,
        trigger: tuple,
        option: tuple,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(trigger)
            ).click()
            WebDriverWait(self._driver, 2).until(
                EC.element_to_be_clickable(option)
            ).click()
            return True
        except (TimeoutException, ElementNotInteractableException):
            return False
        except Exception:
            return False
