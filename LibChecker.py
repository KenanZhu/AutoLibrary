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

from LibOperator import LibOperator


class LibChecker(LibOperator):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver
    ):

        super().__init__(input_queue, output_queue)

        self.__driver = driver


    def _waitResponseLoad(
        self
    ) -> bool:

        pass


    def __navigateToReserveRecordPage(
        self
    ) -> bool:

        try:
            WebDriverWait(self.__driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/history?type=SEAT']"))
            ).click()
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "myReserveList"))
            )
        except:
            self._showTrace("加载预约记录页面失败 !")
            return False
        return True


    def __getReserveRecord(
        self,
        wanted_date: str,
        wanted_status: str
    ) -> dict:

        if wanted_date is None:
            self._showTrace("日期未指定, 无法检查当前预约状态")
            return None
        self._showTrace(f"正在检查用户在日期 {wanted_date} 是否有预约状态为 {wanted_status} 的预约记录......")
        date_obj = datetime.strptime(wanted_date, "%Y-%m-%d").date()

        checked_count = 0
        max_check_times = 3 # we only check (3*4=)12 reservations

        if not self.__navigateToReserveRecordPage():
            return None
        for _ in range(max_check_times):
            try:
                # check if there's any reservation on the date
                reservations = self.__driver.find_elements(
                    By.CSS_SELECTOR, ".myReserveList dl"
                )
            except:
                self._showTrace("加载预约记录失败 !")
                return None
            for i in range(checked_count, len(reservations) - 1): # the last one is load button
                reservation = reservations[i]
                try:
                    time_element = reservation.find_element(
                        By.CSS_SELECTOR, "dt"
                    )
                    info_elements = reservation.find_elements(
                        By.CSS_SELECTOR, "a"
                    )
                except:
                    self._showTrace(f"解析第 {i + 1} 条预约记录时发生未知错误 !")
                    continue
                is_wanted = any(wanted_status in status.text for status in info_elements)
                # process time element to get the date string
                time_str = time_element.text.strip()
                today = datetime.now().date()
                if "明天" in time_str:
                    target_date = today + timedelta(days=1)
                    date_str = target_date.strftime("%Y-%m-%d")
                elif "今天" in time_str:
                    target_date = today
                    date_str = target_date.strftime("%Y-%m-%d")
                elif "昨天" in time_str:
                    target_date = today - timedelta(days=1)
                    date_str = target_date.strftime("%Y-%m-%d")
                else:
                    date_match = re.search(r'(\d{4}-\d{1,2}-\d{1,2})', time_str)
                    if date_match:
                        date_str = date_match.group(1)
                    else:
                        self._showTrace(f"无法解析第 {i + 1} 条预约记录的日期 ! 该记录的时间为 {time_str}")
                        continue
                # reservation is later than the given date, check the next one
                if datetime.strptime(date_str, "%Y-%m-%d").date() > date_obj:
                    continue
                # reservation is earlier than the given date, can reserve
                if datetime.strptime(date_str, "%Y-%m-%d").date() < date_obj:
                    return None
                # query the wanted status
                if is_wanted:
                    self._showTrace(f"寻找到第 {i + 1} 条预约记录, 状态为 {wanted_status}")
                    time_match = re.search(r"(\d{1,2}:\d{2}) -- (\d{1,2}:\d{2})", time_str)
                    if time_match is None:
                        self._showTrace(f"无法解析第 {i + 1} 条预约记录的时间 ! 该记录的时间为 {time_str}")
                        continue
                    return {
                        "index": i,
                        "date": date_str,
                        "time_str": time_match.group(0),
                        "status": wanted_status
                    }
            checked_count = len(reservations) - 1
            # load new reservations if still not sure
            try:
                more_btn = self.__driver.find_element(By.ID, "moreBtn")
                if more_btn.is_displayed() and more_btn.is_enabled():
                    self.__driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                    self.__driver.execute_script("arguments[0].click();", more_btn)
                else:
                    self._showTrace("该用户无法加载更多预约记录")
                    break
            except:
                self._showTrace("加载更多预约记录失败 !")
                break
        return None


    def canReserve(
        self,
        date: str
    ) -> bool:

        # no reserved or using record in the given date
        # then can reserve
        if self.__getReserveRecord(date, "已预约") is None:
            if self.__getReserveRecord(date, "使用中") is None:
                self._showTrace(f"用户在日期 {date} 可以预约")
                return True
            self._showTrace(f"用户在日期 {date} 有使用中的预约, 无法预约")
        self._showTrace(f"用户在日期 {date} 已存在有效预约, 无法预约")
        return False


    def canCheckin(
        self,
        date: str
    ) -> bool:

        # have a reserved record in the given date
        record = self.__getReserveRecord(date, "已预约")
        if record is not None:
            time_match = re.search(r"(\d{1,2}:\d{2})", record["time_str"])
            if time_match:
                begin_time = time_match.group(0)
                begin_time = datetime.strptime(f"{date} {begin_time}", "%Y-%m-%d %H:%M")
                time_diff = datetime.now() - begin_time
                time_diff_seconds = time_diff.total_seconds()
                # before 30 minutes, cant checkin
                if time_diff_seconds < -30*60:
                    self._showTrace(
                        f"用户在日期 {date} 的预约开始时间为 {begin_time}, "
                        f"距离当前时间还有 {abs(time_diff_seconds)/60:.2f} 分钟, 无法签到"
                    )
                    return False
                # before in 30 minutes, can checkin
                elif -30*60 <= time_diff_seconds < 0:
                    self._showTrace(
                        f"用户在日期 {date} 的预约开始时间为 {begin_time}, "
                        f"距离当前时间还有 {abs(time_diff_seconds)/60:.2f} 分钟, 可以签到"
                    )
                    return True
                # past less than 30 minutes, can checkin
                elif 0 <= time_diff_seconds < 30*60:
                    self._showTrace(
                        f"用户在日期 {date} 的预约开始时间为 {begin_time}, "
                        f"当前时间已经 {abs(time_diff_seconds)/60:.2f} 分钟, 可以签到"
                    )
                    return True
            else:
                self._showTrace(f"用户在日期 {date} 的预约时间格式错误, 无法签到")
        self._showTrace(f"用户在日期 {date} 有没有有效预约记录, 无法签到")
        return False
