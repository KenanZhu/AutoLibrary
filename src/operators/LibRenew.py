# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import time
import queue

from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.LibOperator import LibOperator


class LibRenew(LibOperator):

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
            self._showTrace("续约时发生未知错误 !")
            return False
        result_message = result_message_element.text
        if "续约成功" in result_message:
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
                        f"      续约成功 !\n"\
                        f"          {details[1]}\n"\
                        f"          {details[2]}\n"\
                        f"          {details[3]}\n"\
                        f"          {details[4]}")
            else:
                self._showTrace(f"\n"\
                         "      续约成功 !\n"\
                         "          未获取到续约详情 !")
            ok_btn.click()
            return True
        else:
            failure_reason = result_message.replace("续约失败", "").strip()
            self._showTrace(f"\n"\
                "      续约失败 !\n"\
                f"          {failure_reason}"
            )
            ok_btn.click()
            return False

    @staticmethod
    def __timeToMins(
        time_str: str
    ) -> int:

        hour, minute = map(int, time_str.split(":"))
        return hour*60 + minute


    @staticmethod
    def __minsToTime(
        mins: int
    ) -> str:

        hour, minute = divmod(mins, 60)
        return f"{hour:02d}:{minute:02d}"


    def __selectNearstRecord(
        self,
        record: dict,
        reserve_info: dict
    ) -> bool:

        end_time = record["time"]["end"]
        renew_info = reserve_info["renew_time"]
        max_diff = renew_info["max_diff"]
        prefer_earlier = renew_info["prefer_early"]
        target_renew_mins = self.__timeToMins(end_time) + renew_info["expect_duration"]*60
        try:
            WebDriverWait(self.__driver, 2).until(
                EC.visibility_of_element_located((By.ID, "extendDiv"))
            )
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "#extendDiv .renewal_List li")
                )
            )
            renew_ok_btn = WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#extendDiv .btnOK"))
            )
        except:
            self._showTrace("续约时间选择界面加载失败 !")
            return False
        try:
            renew_time_opts = self.__driver.find_elements(
                By.CSS_SELECTOR, "#extendDiv .renewal_List li"
            )
            free_times = []
            best_time_diff = max_diff
            best_actual_diff = None
            best_time_opt = None

            if not renew_time_opts:
                self._showTrace("当前未查询到可用续约时间 !")
                return False
            for time_opt in renew_time_opts:
                time_attr = time_opt.get_attribute("id")
                if time_attr and time_attr.isdigit():
                    time_val = int(time_attr)
                    free_times.append(time_opt.text.strip())
                else:
                    continue
                actual_diff = time_val - target_renew_mins
                abs_diff = abs(actual_diff)
                if abs_diff < best_time_diff or (
                    abs_diff == best_time_diff and (
                        # 优先选择更早的时间
                        (prefer_earlier and actual_diff <= 0) or
                        # 优先选择更晚的时间
                        (not prefer_earlier and actual_diff >= 0)
                    )
                ):
                    best_time_diff = abs_diff
                    best_actual_diff = actual_diff
                    best_time_opt = time_opt

            if best_time_opt is not None:
                best_time_opt.click()
                abs_time_diff = abs(best_actual_diff)
                if best_actual_diff < 0:
                    time_relation = f"早了 {abs_time_diff} 分钟"
                elif best_actual_diff > 0:
                    time_relation = f"晚了 {abs_time_diff} 分钟"
                else:
                    time_relation = f"正好等于续约时间"
                self._showTrace(
                    f"选择距离期望续约时间最近的 {best_time_opt.text}, "\
                    f"与期望续约时间相比 {time_relation}"
                )
                renew_ok_btn.click()
                return True
            self._showTrace(
                "无法选择最近的可用续约时间 !" \
                f"所有可选时间与目标时间相差都超过了 {max_diff} 分钟 !"
            )
            self._showTrace(
                f"当前可供续约的时间有: {free_times}"
            )
            return False
        except:
            self._showTrace("查询可用续约时间时发生未知错误 !")
            return False


    def renew(
        self,
        username: str,
        record: dict,
        reserve_info: dict
    ) -> bool:

        if self.__driver is None:
            self._showTrace("未提供有效 WebDriver 实例 !")
            return False
        try:
            renew_btn = WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.ID, "btnExtend"))
            )
        except:
            self._showTrace(f"用户 {username} 续约界面加载失败 !")
            return False
        if "disabled" in renew_btn.get_attribute("class"):
            self._showTrace(f"用户 {username} 续约按钮不可用, 可能不在场馆内")
            return False
        renew_btn.click()
        if not self.__selectNearstRecord(record, reserve_info):
            return False
        # renew_ok_btn.click()
        if self._waitResponseLoad():
            self._showTrace(f"用户 {username} 续约成功 !")
            return True
        else:
            self._showTrace(f"用户 {username} 续约失败 !")
            return False
