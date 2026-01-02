# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import time
import queue
import base64

import ddddocr

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.LibOperator import LibOperator


class LibLogin(LibOperator):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver: any
    ):

        super().__init__(input_queue, output_queue)

        self.__driver = driver
        self.__ddddocr = ddddocr.DdddOcr()


    def _waitResponseLoad(
        self
    ) -> bool:

        # wait to verify login success
        try:
            WebDriverWait(self.__driver, 2).until( # title contains "自选座位 :: 座位预约系统"
                EC.title_contains("自选座位 :: 座位预约系统")
            )
            WebDriverWait(self.__driver, 2).until( # search button presence
                EC.presence_of_element_located((By.ID, "search"))
            )
            WebDriverWait(self.__driver, 2).until( # select content presence
                EC.presence_of_element_located((By.CLASS_NAME, "selectContent"))
            )
            return True
        except:
            self._showTrace(f"登录页面加载失败 ! : 用户账号或者密码错误/验证码错误, 具体以页面提示为准")
            return False


    def __fillLogInElements(
        self,
        username: str,
        password: str
    ) -> bool:

        # ensure elements presence and fill them
        try:
            username_element = self.__driver.find_element(By.NAME, "username")
            username_element.clear()
            username_element.send_keys(username)
            password_element = self.__driver.find_element(By.NAME, "password")
            password_element.clear()
            password_element.send_keys(password)
        except Exception as e:
            self._showTrace(f"用户名或密码填写失败 ! : {e}")
            return False
        return True


    def __autoRecognizeCaptcha(
        self
    ) -> str:

        # auto recognize captcha
        try:
            captcha_img = self.__driver.find_element(By.ID, "loadImgId")
            img_src = captcha_img.get_attribute("src")
            base64_str = img_src.split(',', 1)[1]
            captcha_img = base64.b64decode(base64_str)
            captcha_text = self.__ddddocr.classification(captcha_img)
            captcha_text = ''.join(filter(str.isalnum, captcha_text)).lower()
            self._showTrace(f"识别到验证码为 : '{captcha_text}'")
            if len(captcha_text) != 4:
                raise Exception("识别到的验证码长度不等于 4 个字符 !")
            return captcha_text
        except Exception as e:
            self._showTrace(f"验证码识别失败 ! : {e}")
            return ""


    def __manualRecognizeCaptcha(
        self
    ) -> str:

        # manual recognize captcha
        try:
            self._showMsg("请输入验证码:")
            captcha_text = self._waitMsg(timeout=15)
            self._showTrace(f"输入的验证码为 : '{captcha_text}'")
            if len(captcha_text) != 4:
                raise Exception("输入的验证码长度不等于 4 个字符 !")
            return captcha_text
        except Exception as e:
            self._showTrace(f"输入验证码失败 ! : {e}")
            return ""


    def __refreshCaptcha(
        self
    ):

        # refresh captcha
        try:
            self._showTrace("刷新验证码......")
            self.__driver.find_element(
                By.ID, "loadImgId"
            ).click()
            return True
        except Exception as e:
            self._showTrace(f"刷新验证码失败 ! : {e}")
            return False


    def __solveCaptcha(
        self,
        auto_captcha: bool = True
    ) -> str:

        max_attempts = 3 # the possibility of 3 times failed is less than (10%^3)
        for _ in range(max_attempts):
            if auto_captcha:
                captcha_text = self.__autoRecognizeCaptcha()
            else:
                self._showTrace(f"用户未配置自动识别验证码, 请手动输入验证码 !")
                captcha_text = self.__manualRecognizeCaptcha()
            if captcha_text:
                return captcha_text
            else:
                if not self.__refreshCaptcha():
                    return ""
        self._showTrace(f"验证码识别失败 {max_attempts} 次, 达到最大尝试次数 !")
        return ""


    def __fillCaptchaElement(
        self,
        captcha_text: str
    ) -> bool:

        try:
            captcha_element = self.__driver.find_element(By.NAME, "answer")
            captcha_element.clear()
            captcha_element.send_keys(captcha_text)
            return True
        except Exception as e:
            self._showTrace(f"验证码填写失败 ! : {e}")
            return False


    def login(
        self,
        username: str,
        password: str,
        max_attempts: int = 5,
        auto_captcha: bool = True
    ) -> bool:

        if self.__driver is None:
            self._showTrace("未提供有效 WebDriver 实例 !")
            return False
        # begin login process
        for attempt in range(max_attempts):
            self._showTrace(f"用户 {username} 第 {attempt + 1} 次尝试登录......")
            if not self.__fillLogInElements(
                username,
                password,
            ):
                continue
            captcha_text = self.__solveCaptcha(auto_captcha)
            if not captcha_text:
                continue
            if not self.__fillCaptchaElement(captcha_text):
                continue
            self._showTrace("尝试登录...")
            try:
                self.__driver.find_element(
                    By.XPATH,
                    "//input[@type='button' and @value='登录']"
                ).click()
            except Exception as e:
                self._showTrace(f"尝试登录失败 ! : {e}")
                continue
            if self._waitResponseLoad():
                self._showTrace(f"用户 {username} 第 {attempt + 1} 次登录成功 !")
                return True
            else:
                self._showTrace(f"用户 {username} 第 {attempt + 1} 次登录失败 !")
        return False
