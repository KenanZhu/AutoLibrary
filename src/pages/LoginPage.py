# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from typing import Callable, Optional

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class LoginPage:

    USERNAME_INPUT   = (By.NAME, "username")
    PASSWORD_INPUT   = (By.NAME, "password")
    CAPTCHA_INPUT    = (By.NAME, "answer")
    CAPTCHA_IMG      = (By.ID,   "loadImgId")
    LOGIN_BUTTON     = (By.XPATH, "//input[@type='button' and @value='登录']")

    SUCCESS_INDICATOR_SEARCH  = (By.ID,        "search")
    SUCCESS_INDICATOR_CONTENT = (By.CLASS_NAME, "selectContent")
    SUCCESS_TITLE_KEYWORD     = "自选座位 :: 座位预约系统"

    PAGE_LOAD_TIMEOUT = 5

    def __init__(
        self,
        driver: WebDriver,
        tracer: Optional[Callable[..., None]] = None,
    ) -> None:

        self._driver: WebDriver = driver
        self._tracer: Optional[Callable[..., None]] = tracer

    def _trace(
        self,
        msg: str,
        level: int = 20,
        no_log: bool = False,
    ) -> None:

        if self._tracer:
            self._tracer(msg, level, no_log)

    def navigate(
        self,
        url: str,
    ) -> bool:

        self._driver.set_page_load_timeout(self.PAGE_LOAD_TIMEOUT)
        self._driver.get(url)
        if not self.waitUntilLoaded():
            return False
        return True

    def waitUntilLoaded(
        self,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.title_contains("首页")
            )
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.USERNAME_INPUT)
            )
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.PASSWORD_INPUT)
            )
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.CAPTCHA_INPUT)
            )
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.CAPTCHA_IMG)
            )
            return True
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception:
            return False

    def fillCredentials(
        self,
        username: str,
        password: str,
    ) -> bool:

        try:
            el = self._driver.find_element(*self.USERNAME_INPUT)
            el.clear()
            el.send_keys(username)
            el = self._driver.find_element(*self.PASSWORD_INPUT)
            el.clear()
            el.send_keys(password)
            return True
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception:
            return False

    def getCaptchaImageSrc(
        self,
    ) -> str:

        captcha_el = self._driver.find_element(*self.CAPTCHA_IMG)
        return captcha_el.get_attribute("src")

    def refreshCaptcha(
        self,
    ) -> bool:

        try:
            self._driver.find_element(*self.CAPTCHA_IMG).click()
            return True
        except (NoSuchElementException, TimeoutException,
                ElementNotInteractableException):
            return False
        except Exception:
            return False

    def fillCaptcha(
        self,
        captcha_text: str,
    ) -> bool:

        try:
            el = self._driver.find_element(*self.CAPTCHA_INPUT)
            el.clear()
            el.send_keys(captcha_text)
            return True
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception:
            return False

    def clickLogin(
        self,
    ) -> bool:

        try:
            self._driver.find_element(*self.LOGIN_BUTTON).click()
            return True
        except (NoSuchElementException, TimeoutException,
                ElementNotInteractableException):
            return False
        except Exception:
            return False

    def waitLoginSuccess(
        self,
    ) -> bool:

        try:
            WebDriverWait(self._driver, 2).until(
                EC.title_contains(self.SUCCESS_TITLE_KEYWORD)
            )
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.SUCCESS_INDICATOR_SEARCH)
            )
            WebDriverWait(self._driver, 2).until(
                EC.presence_of_element_located(self.SUCCESS_INDICATOR_CONTENT)
            )
            return True
        except (NoSuchElementException, TimeoutException):
            return False
        except Exception:
            return False

    def stopPageLoad(
        self,
    ) -> None:

        self._driver.execute_script("window.stop();")

    def login(
        self,
        username: str,
        password: str,
        captcha_solver: Callable[["LoginPage", bool], str],
        auto_captcha: bool,
        max_attempts: int = 5,
    ) -> bool:

        for attempt in range(max_attempts):
            self._trace(
                f"用户 {username} 第 {attempt + 1} 次尝试登录......",
                no_log=True,
            )
            if not self.fillCredentials(username, password):
                continue
            captcha_text = captcha_solver(self, auto_captcha)
            if not captcha_text:
                continue
            if not self.fillCaptcha(captcha_text):
                continue
            self._trace("尝试登录...", no_log=True)
            if not self.clickLogin():
                continue
            if self.waitLoginSuccess():
                self._trace(f"用户 {username} 第 {attempt + 1} 次登录成功 !")
                return True
            else:
                self._trace(
                    "登录页面加载失败 ! : "
                    "用户账号或者密码错误/验证码错误, 具体以页面提示为准",
                    level=40,
                )
        return False
