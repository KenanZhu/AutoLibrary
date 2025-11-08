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

    @staticmethod
    def __formatDiffTime(
        seconds: float
    ) -> str:

        hours = int(seconds // 3600)
        minutes = int(seconds % 3600 // 60)
        seconds = int(seconds % 60)
        return f"{hours} 时 {minutes} 分 {seconds} 秒"


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


    def __decodeReserveInfo(
        self,
        info_elements
    ) -> str:

        location = ""
        status = ""
        for info in info_elements:
            if "已预约" in info.text:
                status = "已预约"
            elif "使用中" in info.text:
                status = "使用中"
            elif "已完成" in info.text:
                status = "已完成"
            elif "已结束使用" in info.text:
                status = "已结束使用"
            elif "已取消" in info.text:
                status = "已取消"
            elif "失约" in info.text:
                status = "失约"
            elif "图书馆" in info.text:
                location = info.text.strip()
        return {
            "location": location,
            "status": status,
        }


    def __decodeReserveRecord(
        self,
        reservation
    ) -> dict:

        try:
            time_element = reservation.find_element(
                By.CSS_SELECTOR, "dt"
            )
            info_elements = reservation.find_elements(
                By.CSS_SELECTOR, "a"
            )
        except:
            return None
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
            date_match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", time_str)
            if date_match:
                date_str = date_match.group(1)
            else:
                date_str = ""
        time_match = re.search(r"(\d{1,2}:\d{2}) -- (\d{1,2}:\d{2})", time_str)
        if time_match:
            begin_time = time_match.group(1)
            end_time = time_match.group(2)
        else:
            time_str = ""
        info = self.__decodeReserveInfo(info_elements)
        return {
            "date": date_str,
            "time": {
                "begin": begin_time,
                "end": end_time,
            },
            "info": info
        }


    def __getReserveRecord(
        self,
        wanted_date: str,
        wanted_status: str
    ) -> dict:

        if wanted_date is None:
            self._showTrace("日期未指定, 无法检查当前预约状态")
            return None
        self._showTrace(f"正在检查用户在 {wanted_date} 是否有预约状态为 {wanted_status} 的预约记录......")
        date_obj = datetime.strptime(wanted_date, "%Y-%m-%d").date()

        checked_count = 0
        max_check_times = 6 # we only check (4*(6-1)=)20 reservations, the last time cant be checked

        if not self.__navigateToReserveRecordPage():
            return None
        for _ in range(max_check_times):
            try:
                # check if there's any reservation on the date
                WebDriverWait(self.__driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".myReserveList > dl"))
                )
                reservations = self.__driver.find_elements(
                    By.CSS_SELECTOR, ".myReserveList > dl:not(#moreBlock)"
                )
            except:
                self._showTrace("加载预约记录失败 !")
                return None
            for i in range(checked_count, len(reservations)): # the last one is load button
                reservation = reservations[i]
                record = self.__decodeReserveRecord(reservation)
                if record is None:
                    continue
                record_date = record["date"]
                record_time = record["time"]
                status = record["info"]["status"]
                location = record["info"]["location"]
                if record_date == "" or record_time == {"begin": "", "end": ""}:
                    continue
                is_wanted = (status == wanted_status)
                # reservation is later than the given date, check the next one
                if datetime.strptime(record_date, "%Y-%m-%d").date() > date_obj:
                    continue
                # reservation is earlier than the given date, can reserve
                if datetime.strptime(record_date, "%Y-%m-%d").date() < date_obj:
                    return None
                # query the wanted status
                if is_wanted:
                    self._showTrace(
                        f"寻找到用户第 {i + 1} 条状态为 {wanted_status} 的预约记录, "
                        f"详细信息: {record_date} {record_time['begin']} - {record_time['end']} {location}"
                    )
                    return {
                        "index": i,
                        "date": record_date,
                        "time": record_time,
                        "status": wanted_status
                    }
            checked_count = len(reservations)
            # load new reservations if still not sure
            try:
                more_btn = self.__driver.find_element(By.ID, "moreBtn")
                if more_btn.is_displayed() and more_btn.is_enabled():
                    self.__driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                    self.__driver.execute_script("arguments[0].click();", more_btn)
                else:
                    self._showTrace("用户无法加载更多预约记录")
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
                self._showTrace(f"用户在 {date} 可以预约")
                return True
            self._showTrace(f"用户在 {date} 有使用中的预约, 无法预约")
            return False
        self._showTrace(f"用户在 {date} 已存在有效预约, 无法预约")
        return False


    def canCheckin(
        self,
        date: str
    ) -> bool:

        # have a reserved record in the given date
        record = self.__getReserveRecord(date, "已预约")
        if record is not None:
            begin_time = record["time"]["begin"]
            begin_time = datetime.strptime(f"{date} {begin_time}", "%Y-%m-%d %H:%M")
            time_diff = datetime.now() - begin_time
            time_diff_seconds = time_diff.total_seconds()
            # before 30 minutes, cant checkin
            if time_diff_seconds < -30*60:
                self._showTrace(
                    f"用户在 {date} 的预约开始时间为 {begin_time}, "
                    f"距离当前时间还有 {self.__formatDiffTime(abs(time_diff_seconds))}, 无法签到"
                )
                return False
            # before in 30 minutes, can checkin
            elif -30*60 <= time_diff_seconds < 0:
                self._showTrace(
                    f"用户在 {date} 的预约开始时间为 {begin_time}, "
                    f"距离当前时间还有 {self.__formatDiffTime(abs(time_diff_seconds))}, 可以签到"
                )
                return True
            # past less than 30 minutes, can checkin
            elif 0 <= time_diff_seconds < 30*60:
                self._showTrace(
                    f"用户在 {date} 的预约开始时间为 {begin_time}, "
                    f"当前时间已经 {self.__formatDiffTime(abs(time_diff_seconds))}, 可以签到"
                )
                return True
        self._showTrace(f"用户在 {date} 没有有效预约记录, 无法签到")
        return False


    def canRenew(
        self,
        date: str
    ) -> bool:

        # have a using record in the given date
        record = self.__getReserveRecord(date, "使用中")
        if record is not None:
            end_time = record["time"]["end"]
            end_time = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            time_diff = end_time - datetime.now()
            time_diff_seconds = time_diff.total_seconds()
            # a using record is definitely after the begin time
            if abs(time_diff_seconds) < 120*60:
                self._showTrace(
                    f"用户在 {date} 的预约结束时间为 {end_time}, "
                    f"距离当前时间还有 {self.__formatDiffTime(abs(time_diff_seconds))}, 可以续约"
                )
                return True
            else:
                self._showTrace(
                    f"用户在 {date} 的预约结束时间为 {end_time}, "
                    f"距离当前时间还有 {self.__formatDiffTime(abs(time_diff_seconds))}, 无法续约"
                )
                return False
        self._showTrace(f"用户在 {date} 没有有效预约记录, 无法续约")
        return False
