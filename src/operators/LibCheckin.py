# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import re
import time
import queue

from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.LibOperator import LibOperator


class LibCheckin(LibOperator):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver: any
    ):

        super().__init__(input_queue, output_queue)

        self.__driver = driver


    def _waitResponseLoad(
        self
    ) -> bool:

        try:
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ui_dialog"))
            )
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "resultMessage"))
            )
            WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "btnOK"))
            )
            result_message_element = self.__driver.find_element(
                By.CLASS_NAME, "resultMessage"
            )
            ok_btn = self.__driver.find_element(By.CLASS_NAME, "btnOK")
        except:
            self._showTrace("签到时发生未知错误 !")
            return False
        result_message = result_message_element.text
        if "签到成功" in result_message:
            try:
                detail_elements = self.__driver.find_elements(
                    By.CSS_SELECTOR, ".resultMessage dd"
                )
            except:
                pass
            if detail_elements:
                details = [element.text for element in detail_elements if element.text.strip()]
                if len(details) >= 5:
                    self._showTrace(f"\n"\
                        f"      签到成功 !\n"\
                        f"          {details[1]}\n"\
                        f"          {details[2]}\n"\
                        f"          {details[3]}\n"\
                        f"          {details[4]}"
                    )
            else:
                self._showTrace(f"\n"\
                         "      签到成功 !\n"\
                         "          未获取到签到详情 !"
                    )
            ok_btn.click()
            return True
        else:
            failure_reason = result_message.replace("签到失败", "").strip()
            self._showTrace(f"\n"\
                "      签到失败 !\n"\
                f"          {failure_reason}"
                )
            ok_btn.click()
            return False


    def checkin(
        self,
        username: str
    ) -> bool:

        if self.__driver is None:
            self._showTrace("未提供有效 WebDriver 实例 !")
            return False
        try:
            checkin_btn = WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.ID, "btnCheckIn"))
            )
        except:
            self._showTrace(f"用户 {username} 签到界面加载失败 !")
            return False
        if "disabled" in checkin_btn.get_attribute("class"):
            self._showTrace("签到按钮不可用, 可能不在场馆内, 请连接图书馆网络后重试")
            return False
        checkin_btn.click()
        if self._waitResponseLoad():
            self._showTrace(f"用户 {username} 签到成功 !")
            return True
        else:
            self._showTrace(f"用户 {username} 签到失败 !")
        return False
