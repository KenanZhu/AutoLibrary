# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Dialog:
    """
        Context-managed overlay / modal / dialog on a page.

        Automates the lifecycle: wait for appearance on enter,
        optionally wait for disappearance on exit.
    """

    def __init__(
        self,
        driver: WebDriver,
        root_locator: tuple,
        auto_close_on_exit: bool = True,
        wait_timeout: float = 3.0,
    ) -> None:

        self._driver: WebDriver = driver
        self._root_locator: tuple = root_locator
        self._auto_close: bool = auto_close_on_exit
        self._timeout: float = wait_timeout

    def __enter__(
        self,
    ) -> "Dialog":

        WebDriverWait(self._driver, self._timeout).until(
            EC.visibility_of_element_located(self._root_locator)
        )
        return self

    def __exit__(
        self,
        *args: object,
    ) -> None:

        if self._auto_close:
            WebDriverWait(self._driver, self._timeout).until(
                EC.invisibility_of_element_located(self._root_locator)
            )

    def _find(
        self,
        by: str,
        value: str,
    ) -> WebElement:

        return self._driver.find_element(by, value)

    def _findAll(
        self,
        by: str,
        value: str,
    ) -> list[WebElement]:

        return self._driver.find_elements(by, value)

    def _waitClickable(
        self,
        locator: tuple,
        timeout: float = 2.0,
    ) -> WebElement:

        return WebDriverWait(self._driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    def _waitPresence(
        self,
        locator: tuple,
        timeout: float = 2.0,
    ) -> WebElement:

        return WebDriverWait(self._driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def _waitVisible(
        self,
        locator: tuple,
        timeout: float = 2.0,
    ) -> WebElement:

        return WebDriverWait(self._driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def _waitAllPresence(
        self,
        locator: tuple,
        timeout: float = 2.0,
    ) -> list[WebElement]:

        return WebDriverWait(self._driver, timeout).until(
            EC.presence_of_all_elements_located(locator)
        )
