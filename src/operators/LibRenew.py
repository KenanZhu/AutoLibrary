# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.LibTimeSelector import LibTimeSelector


class LibRenew(LibTimeSelector):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver: WebDriver
    ):

        super().__init__(input_queue, output_queue)

        self.__driver = driver


    def _waitResponseLoad(
        self
    ) -> bool:

        self.__driver.refresh()
        return True


    def __waitRenewDialog(
        self
    ) -> bool:

        try:
            WebDriverWait(self.__driver, 2).until(
                EC.visibility_of_element_located((By.ID, "extendDiv"))
            )
            head_message = WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#extendDiv p.messageHead"))
            )
            result_message = WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#extendDiv div.resultMessage"))
            )
        except:
            self._showTrace("续约时间选择界面加载失败 !", self.TraceLevel.ERROR)
            return False
        head_message = head_message.text.strip()
        if "警告" in head_message:
            result_message = result_message.text.strip()
            self._showTrace(f"\n"\
                f"      续约失败 !\n"\
                f"          {result_message}", no_log=True)
            return False
        try:
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "#extendDiv .renewal_List li")
                )
            )
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#extendDiv .btnOK"))
            )
        except:
            self._showTrace("续约时间选择界面加载失败 !", self.TraceLevel.ERROR)
            return False
        return True


    def __selectNearestTime(
        self,
        record: dict,
        reserve_info: dict
    ) -> bool:

        """
            Select the nearest available renewal time.
        """
        end_time = record["time"]["end"]
        renew_info = reserve_info["renew_time"]
        max_diff = renew_info["max_diff"]
        prefer_earlier = renew_info["prefer_early"]
        target_renew_mins = self._timeStrToMins(end_time) + renew_info["expect_duration"]*60

        # Validate and adjust target renew time to library closing time
        if not self.__validateAndAdjustRenewTime(end_time, target_renew_mins):
            return False
        renew_ok_btn = self.__driver.find_element(By.CSS_SELECTOR, "#extendDiv .btnOK")
        renew_time_opts = self.__driver.find_elements(By.CSS_SELECTOR, "#extendDiv .renewal_List li")
        if not renew_time_opts:
            self._showTrace("当前未查询到可用续约时间 !", self.TraceLevel.WARNING)
            return False

        # Find best renewal time option
        best_opt, best_text, actual_diff, free_times = self._findBestTimeOption(
            renew_time_opts, target_renew_mins, max_diff, prefer_earlier, is_reserve=False
        )
        if best_opt is not None:
            return self.__confirmRenewal(best_opt, best_text, actual_diff, record, renew_ok_btn)
        self._showTrace(
            "无法选择最近的可用续约时间 ! "
            f"所有可选时间与目标时间相差都超过了 {max_diff} 分钟 !",
            self.TraceLevel.WARNING
        )
        self._showTrace(f"当前可供续约的时间有: {free_times}")
        return False


    def __validateAndAdjustRenewTime(
        self,
        end_time: str,
        target_renew_mins: int
    ) -> bool:

        """
            Validate and adjust renewal time to library closing time if needed.
        """
        LIBRARY_CLOSE_TIME = 1410  # 23:30 in minutes
        if target_renew_mins > LIBRARY_CLOSE_TIME:
            actual_renew_duration = LIBRARY_CLOSE_TIME - self._timeStrToMins(end_time)
            if actual_renew_duration <= 0:
                self._showTrace(f"当前结束时间 {end_time} 已接近闭馆时间,无法续约 !", self.TraceLevel.ERROR)
                return False
            self._showTrace(
                f"续约时间已调整至闭馆时间 {self._minsToTimeStr(LIBRARY_CLOSE_TIME)},"
                f"实际续约时长为 {actual_renew_duration//60} 小时 {actual_renew_duration%60} 分钟"
            )
            return True
        return True


    def __confirmRenewal(
        self,
        best_opt,
        best_text: str,
        actual_diff: int,
        record: dict,
        ok_btn
    ) -> bool:

        """
            Confirm the selected renewal time.
        """
        try:
            best_opt.click()
            abs_diff = abs(actual_diff)
            time_relation = self._formatTimeRelation(abs_diff, actual_diff, "续约时间")
            self._showTrace(
                f"选择距离期望续约时间最近的 {best_text}, "
                f"与期望续约时间相比 {time_relation}"
            )
            record["time"]["end"] = best_text.strip()
            ok_btn.click()
            return True
        except:
            self._showTrace("确认续约时发生错误 !", self.TraceLevel.ERROR)
            return False


    def renew(
        self,
        username: str,
        record: dict,
        reserve_info: dict
    ) -> bool:

        if self.__driver is None:
            self._showTrace("未提供有效 WebDriver 实例 !", self.TraceLevel.WARNING)
            return False
        try:
            renew_btn = WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.ID, "btnExtend"))
            )
        except:
            self._showTrace(f"用户 {username} 续约界面加载失败 !", self.TraceLevel.ERROR)
            return False
        if "disabled" in renew_btn.get_attribute("class"):
            self._showLog(f"用户 {username} 续约按钮不可用, 可能不在场馆内")
            self._showTrace(f"用户 {username} 续约按钮不可用, 可能不在场馆内, 请连接图书馆网络后重试", no_log=True)
            return False
        renew_btn.click()
        if not self.__waitRenewDialog():
            self._showTrace(f"用户 {username} 续约失败 !", self.TraceLevel.ERROR)

            # After the renewal, the webpage will display a mask overlay,
            # so we need to refresh the page for subsequent operations.
            self.__driver.refresh()
            return False
        if not self.__selectNearestTime(record, reserve_info):
            self._showTrace(f"用户 {username} 续约失败 !", self.TraceLevel.ERROR)
            self.__driver.refresh()
            return False
        if self._waitResponseLoad():
            return True
