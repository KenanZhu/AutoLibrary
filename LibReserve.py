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


class LibReserve(LibOperator):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver
    ):

        super().__init__(input_queue, output_queue)

        self.__driver = driver
        # library floor and room mapping in website
        self.__floor_map = {
            "2": "二层",
            "3": "三层",
            "4": "四层",
            "5": "五层"
        }
        self.__room_map = {
            "1": "二层内环",
            "2": "二层外环",
            "3": "三层内环",
            "4": "三层外环",
            "5": "四层内环",
            "6": "四层外环",
            "7": "四层期刊区",
            "8": "五层考研"
        }


    def _waitResponseLoad(
        self,
    ) -> bool:

        try:
            WebDriverWait(self.__driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "layoutSeat"))
            )
            title_elements = []
            # reserve failed without title elements, so we need to try
            try:
                WebDriverWait(self.__driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".layoutSeat dt"))
                )
                title_elements = self.__driver.find_elements(
                    By.CSS_SELECTOR, ".layoutSeat dt"
                )
            except:
                pass
            content_elements = self.__driver.find_elements(
                By.CSS_SELECTOR, ".layoutSeat dd"
            )
            if not content_elements:
                 self._showTrace("未找到预约结果")
                 raise
            title = title_elements[0].text if title_elements else ""
            contents = [element.text for element in content_elements if element.text.strip()]
            for message in contents:
               if "预约失败" in message or "已有1个有效预约" in message:
                   self._showTrace(f"预约失败 - {"".join(contents)}")
                   raise
            if "预定好了" in title or "预约成功" in title or "操作成功" in title:
                if len(contents) >= 6:
                    date_val = contents[1].split(" ： ")[1].strip() if " ： " in contents[1] else contents[1].strip()
                    time_val = contents[2].split(" ： ")[1].strip() if " ： " in contents[2] else contents[2].strip()
                    seat_val = contents[3].split(" ： ")[1].strip() if " ： " in contents[3] else contents[3].strip()
                    checkin_val = contents[5].strip()
                    self._showTrace(f"\n"\
                        f"      预约成功 !\n"\
                        f"          预约日期: {date_val}, \n"\
                        f"          预约时间: {time_val}, \n"\
                        f"          预约座位: {seat_val}, \n"\
                        f"          签到时间: {checkin_val}")
                else:
                    self._showTrace(f"\n"\
                        f"      预约成功 !\n"\
                        f"          未找获取到详细信息")
            return True
        except:
            self._showTrace(f"预约结果加载失败 !")
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


    def __checkReserveInfo(
        self,
        reserve_info: dict
    ) -> bool:

        try:
            # check the required information
            # reserve_info["place"]
            if reserve_info.get("floor") is None:
                raise ValueError("未指定楼层")
            if reserve_info["floor"] not in self.__floor_map:
                raise ValueError(f"楼层 '{reserve_info['floor']}' 不存在")
            if reserve_info.get("room") is None:
                raise ValueError("未指定房间")
            if reserve_info["room"] not in self.__room_map:
                raise ValueError(f"房间 '{reserve_info['room']}' 不存在")
            if reserve_info.get("seat_id") is None:
                raise ValueError("未指定座位")
        except ValueError as e:
            self._showTrace(
                f"预约信息错误 ! : {e}, "\
                f"由于缺少必要的预约信息， 无法开始预约流程, 请检查预约信息是否完整"
            )
            return False

        # check and try to fix the time errors
        cur_time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime())
        cur_date, curr_time = cur_time_str.split()
        if not reserve_info.get("date"):
            reserve_info["date"] = cur_date
            self._showTrace(f"预约日期未指定, 自动设置为当前日期: {cur_date}")
        else:
            if reserve_info["date"] < cur_date:
                self._showTrace(
                    f"预约日期错误 ! :"\
                    f"{reserve_info['date']} 早于当前日期 {cur_date}, 自动设置为当前日期"
                )
                reserve_info["date"] = cur_date
        # check the begin time
        begin_time = reserve_info.get("begin_time")
        if not begin_time:
            reserve_info["begin_time"] = {
                "time": curr_time,
                "max_diff": 30,
                "prefer_early": True
            }
            self._showTrace(f"开始时间未指定, 自动设置为当前时间: {curr_time}, 最大时间差为 30 分钟, 优先选择更早预约时间")
        else:
            begin_time = reserve_info["begin_time"]
            if "time" not in begin_time:
                begin_time["time"] = curr_time
                self._showTrace(f"开始时间未指定, 自动设置为当前时间: {curr_time}")
            if "max_diff" not in begin_time:
                begin_time["max_diff"] = 30
                self._showTrace(f"最大时间差未指定, 自动设置为 30 分钟")
            if "prefer_early" not in begin_time:
                begin_time["prefer_early"] = True
                self._showTrace(f"是否优先选择更早预约时间未指定, 自动设置为 True")
        expect_duration = reserve_info.get("expect_duration")
        if not expect_duration:
            reserve_info["expect_duration"] = 4
            expect_duration = 4
            self._showTrace("预约持续时间未指定, 使用默认时长为 4 小时")
        if not reserve_info.get("satisfy_duration"):
            reserve_info["satisfy_duration"] = True
            self._showTrace("预约满足时长要求未指定, 默认满足")
        # check the end time
        if not reserve_info.get("end_time"):
            begin_mins = self.__timeToMins(reserve_info["begin_time"]["time"])
            end_mins = begin_mins + reserve_info["expect_duration"] * 60
            end_time_str = self.__minsToTime(end_mins)
            reserve_info["end_time"] = {
                "time": end_time_str,
                "max_diff": 30,
                "prefer_early": False
            }
            self._showTrace(f"结束时间未指定, 自动设置为开始时间加上期望时长: {end_time_str}, 最大时间差为 30 分钟, 优先选择较晚预约时间")
        else:
            end_time = reserve_info["end_time"]
            if "time" not in end_time:
                begin_mins = self.__timeToMins(reserve_info["begin_time"]["time"])
                end_mins = begin_mins + reserve_info["expect_duration"] * 60
                end_time["time"] = self.__minsToTime(end_mins)
                self._showTrace(f"结束时间未指定, 自动设置为开始时间加上期望时长: {end_time['time']}")
            if "max_diff" not in end_time:
                end_time["max_diff"] = 30
                self._showTrace(f"最大时间差未指定, 自动设置为 30 分钟")
            if "prefer_early" not in end_time:
                end_time["prefer_early"] = False
                self._showTrace(f"是否优先选择较早预约时间未指定, 自动设置为 False")
        # check the reserve time boundary and fix the errors
        #
        # get time string for message show
        begin_time_str = reserve_info["begin_time"]["time"]
        end_time_str = reserve_info["end_time"]["time"]

        # minute time for check and fix them
        begin_mins = self.__timeToMins(begin_time_str)
        end_mins = self.__timeToMins(end_time_str)

        # ensure begin time is not later than end time
        if begin_mins > end_mins:
            reserve_info["begin_time"]["time"], reserve_info["end_time"]["time"] = end_time_str, begin_time_str
            reserve_info["begin_time"]["prefer_early"], reserve_info["end_time"]["prefer_early"] = \
                reserve_info["end_time"]["prefer_early"], reserve_info["begin_time"]["prefer_early"]
            self._showTrace("预约开始时间晚于预约结束时间，自动调换开始时间和结束时间")

            # update the begin_mins and end_mins after swap
            begin_time_str, end_time_str = end_time_str, begin_time_str
            begin_mins, end_mins = end_mins, begin_mins

        # ensure end time is not later than 22:30
        max_end_mins = self.__timeToMins("22:30")
        if end_mins > max_end_mins:
            reserve_info["end_time"]["time"] = "22:30"
            end_time_str = "22:30"
            end_mins = max_end_mins
            self._showTrace("预约结束时间超过 22:30, 自动设置为 22:30")

        # ensure expect duration is shorter than 8 hours
        max_duration_mins = 8 * 60
        duration_mins = end_mins - begin_mins
        if duration_mins > max_duration_mins:
            new_end_mins = begin_mins + max_duration_mins
            reserve_info["end_time"]["time"] = self.__minsToTime(new_end_mins)
            self._showTrace("预约持续时间超过8小时, 自动设置为 8 小时")
        self._showTrace(
            f"预约信息检查完成，准备预约 "
            f"{reserve_info['date']} "
            f"{reserve_info['begin_time']["time"]} - "
            f"{reserve_info['end_time']["time"]} "
            f"图书馆 "
            f"{self.__floor_map[reserve_info['floor']]} "
            f"{self.__room_map[reserve_info['room']]} "
            f"的座位 {reserve_info['seat_id']}"
        )
        return True


    def __clickElement(
        self,
        trigger_locator: tuple,
        fail_msg: str,
        success_msg: str,
        option_locator: tuple = None,
    ) -> bool:

        try:
            # click the trigger element
            WebDriverWait(self.__driver, 5).until(
                EC.element_to_be_clickable(trigger_locator)
            ).click()
            if option_locator:
                # select the option element if specified
                WebDriverWait(self.__driver, 5).until(
                    EC.element_to_be_clickable(option_locator)
                ).click()
            self._showTrace(success_msg)
            return True
        except:
            self._showTrace(fail_msg)
            return False


    def __selectDate(
        self,
        date_str: str
    ) -> bool:

        return self.__clickElement(
            trigger_locator=(By.ID, "onDate_select"),
            option_locator=(By.XPATH, f"//p[@id='options_onDate']/a[@value='{date_str}']"),
            success_msg=f"日期 {date_str} 选择成功 !",
            fail_msg=f"选择日期失败 ! : {date_str} 不可用"
        )


    def __selectPlace(
        self,
        place: str
    ) -> bool:

        actual_place = "1" if place == "图书馆" else "1"
        return self.__clickElement(
            trigger_locator=(By.ID, "display_building"),
            option_locator=(By.XPATH, f"//p[@id='options_building']/a[@value='{actual_place}']"),
            success_msg=f"预约场所 {place} 选择成功 !",
            fail_msg=f"选择预约场所失败 ! : {place} 不可用"
        )


    def __selectFloor(
        self,
        floor: str
    ) -> bool:

        display_floor = self.__floor_map.get(floor)
        return self.__clickElement(
            trigger_locator=(By.ID, "floor_select"),
            option_locator=(By.XPATH, f"//p[@id='options_floor']/a[@value='{floor}']"),
            success_msg=f"楼层 {display_floor} 选择成功 !",
            fail_msg=f"选择楼层失败 ! : {display_floor} 不可用"
        )


    def __selectRoom(
        self,
        room: str
    ) -> bool:

        display_room = self.__room_map.get(room)
        return self.__clickElement(
            trigger_locator=(By.ID, f"room_{room}"),
            option_locator=None,
            success_msg=f"房间 {display_room} 选择成功 !",
            fail_msg=f"选择房间失败 ! : {display_room} 不可用"
        )


    def __selectSeat(
        self,
        seat_id: str
    ) -> bool:

        try:
            # wait fot seat layout element to load
            WebDriverWait(self.__driver, 5).until(
                EC.presence_of_element_located((By.ID, "seatLayout"))
            )
            all_seats = self.__driver.find_elements(
                By.CSS_SELECTOR, "li[id^='seat_']"
            )
            seat_id_upper = seat_id.lstrip('0').upper()
            for seat in all_seats:
                if not seat_id_upper == seat.text.lstrip('0'):
                    continue
                seat_link = seat.find_element(By.TAG_NAME, "a")
                WebDriverWait(self.__driver, 5).until(
                    EC.element_to_be_clickable(seat_link)
                )
                seat_link.click()
                seat_status = seat_link.get_attribute("title")
                self._showTrace(f"座位 {seat_id} 选择成功 ! : 当前状态 - '{seat_status}'")
                return True
            self._showTrace(f"座位 {seat_id} 在该楼层区域中不存在, 请检查座位号是否正确")
        except:
            self._showTrace(f"座位选择失败 !")
            return False


    def __selectNearestTime(
        self,
        time_id: str,
        time_type: str,
        target_time: int,
        max_time_diff: int = 30,
        prefer_earlier: bool = True
    ) -> int:

        try:
            all_time_opts = self.__driver.find_elements(
                By.CSS_SELECTOR,
                f"#{time_id} ul li a"
            )
            free_times = []
            best_time_diff = max_time_diff
            best_actual_diff = None
            best_time_opt = None

            for time_opt in all_time_opts:
                time_attr = time_opt.get_attribute("time")
                if time_attr == "now":
                    now = datetime.now()
                    time_val = int(now.hour*60 + now.minute)
                elif time_attr and time_attr.isdigit():
                    time_val = int(time_attr)
                else:
                    continue
                free_times.append(self.__minsToTime(time_val))
                actual_diff = time_val - target_time
                abs_diff = abs(actual_diff)
                if abs_diff < best_time_diff or (
                    abs_diff == best_time_diff and (
                        # prefer earlier time
                        (prefer_earlier and actual_diff < 0) or
                        # prefer later time
                        (not prefer_earlier and actual_diff > 0)
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
                    time_relation = f"正好等于 {time_type}"
                target_time += best_actual_diff
                self._showTrace(
                    f"选择距离期望 {time_type} 最近的 {best_time_opt.text}, "\
                    f"与期望 {time_type} 相比 {time_relation}"
                )
                return target_time
            self._showTrace(
                f"无法选择最近的 {time_type} {self.__minsToTime(target_time)}, "\
                f"所有可选时间与目标时间相差都超过 {max_time_diff} 分钟"
            )
            self._showTrace(f"当前可供预约的 {time_type} 有: {free_times}")
            return -1
        except:
            self._showTrace(f"{time_type} {self.__minsToTime(target_time)} 选择失败 !")
            return -1


    def __selectSeatTime(
        self,
        begin_time: dict,
        end_time: dict,
        expct_duration: int = 4,
        satisfy_duration: bool = True
    ) -> bool:

        expect_begin_time = actual_begin_time = begin_time["time"]
        expect_end_time = actual_end_time = end_time["time"]
        expect_begin_mins = self.__timeToMins(expect_begin_time)
        expect_end_mins = self.__timeToMins(expect_end_time)

        # select the begin time
        if self.__selectNearestTime(
            time_id="startTime", # dont change into begin, this is the element in the page
            time_type="开始时间",
            target_time=expect_begin_mins,
            max_time_diff=begin_time["max_diff"],
            prefer_earlier=begin_time["prefer_early"]
        ) == -1:
            return False
        else:
            actual_begin_time = self.__minsToTime(expect_begin_mins)
        # if 'satisfy_duration' is True.
        # select the end time based on the begin time
        # (because it may be changed under the 'max time diff' strategy) and expect duration.
        if satisfy_duration:
            expect_end_mins = int(expect_begin_mins + expct_duration*60)
            self._showTrace(
                f"需要满足期望预约持续时间: {expct_duration} 小时, "\
                f"根据开始时间 {actual_begin_time} 计算结束时间: {self.__minsToTime(expect_end_mins)}"
            )
        # select the end time
        if self.__selectNearestTime(
            time_id="endTime",
            time_type="结束时间",
            target_time=expect_end_mins,
            max_time_diff=end_time["max_diff"],
            prefer_earlier=end_time["prefer_early"]
        ) == -1:
            return False
        else:
            actual_end_time = self.__minsToTime(expect_end_mins)
        self._showTrace(
            f"期望预约时间段: {expect_begin_time} - {expect_end_time}, "
            f"实际预约时间段: {actual_begin_time} - {actual_end_time}"
        )
        return True


    def canReserve(
        self,
        date: str
    ) -> bool:

        if date is None:
            self._showTrace("日期未指定, 无法检查预约状态")
            return True
        else:
            self._showTrace(f"正在检查用户在日期 {date} 是否可预约......")
            date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        try:
            # we need to navigate to the history page to check if we can reserve
            WebDriverWait(self.__driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/history?type=SEAT']"))
            ).click()
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "myReserveList"))
            )
            WebDriverWait(self.__driver, 2).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".myReserveList dl"))
            )
        except:
            self._showTrace("加载预约记录页面失败 !")
            return False
        checked_count = 0
        max_attemots = 3 # we only check (3*4=)12 reservations

        for _ in range(max_attemots):
            try:
                # check if there's any reservation on the date
                reservations = self.__driver.find_elements(
                    By.CSS_SELECTOR, ".myReserveList dl"
                )
            except:
                self._showTrace("加载预约记录失败 !")
                return False
            for i in range(checked_count, len(reservations) - 1): # the last one is load button
                reservation = reservations[i]
                try:
                    time_element = reservation.find_element(
                        By.CSS_SELECTOR, "dt"
                    )
                    status_elements = reservation.find_elements(
                        By.CSS_SELECTOR, "a"
                    )
                    is_reserved = any("已预约" in status.text for status in status_elements)
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
                            continue
                    # reservation is earlier than the given date, can reserve
                    if datetime.strptime(date_str, "%Y-%m-%d").date() < date_obj:
                        self._showTrace(f"用户在 {date} 可预约")
                        return True
                    # reservation is later than the given date, check the next one
                    elif datetime.strptime(date_str, "%Y-%m-%d").date() > date_obj:
                        continue
                    # compare with the given date
                    if date_str == date and is_reserved:
                        self._showTrace(f"用户在 {date} 已存在有效预约, 无法预约")
                        return False
                except:
                    self._showTrace(f"解析第 {i + 1} 条预约记录时发生未知错误 !")
                    continue
            checked_count = len(reservations) - 1
            # load new reservations if still not sure
            try:
                more_btn = self.__driver.find_element(By.ID, "moreBtn")
                if more_btn.is_displayed() and more_btn.is_enabled():
                    self.__driver.execute_script("arguments[0].scrollIntoView(true);", more_btn)
                    self.__driver.execute_script("arguments[0].click();", more_btn)
                else:
                    break
            except:
                break
        self._showTrace(f"用户在 {date} 可预约")
        return True


    def reserve(
        self,
        reserve_info: dict
    ) -> bool:

        submit_reserve = False
        reserve_success = False
        have_hover_on_page = False

        # reserve info
        if not self.__checkReserveInfo(reserve_info):
            return False
        # map page
        try:
            WebDriverWait(self.__driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/map']"))
            ).click()
            WebDriverWait(self.__driver, 5).until(
                EC.presence_of_element_located((By.ID, "seatLayout"))
            )
        except:
            self._showTrace(f"加载预约选座页面失败 !")
            return False
        # date, place, floor
        if not self.__selectDate(reserve_info["date"]):
            return False
        if not self.__selectPlace(reserve_info["place"]):
            return False
        if not self.__selectFloor(reserve_info["floor"]):
            return False
        # room find
        try:
            WebDriverWait(self.__driver, 5).until(
                EC.element_to_be_clickable((By.ID, "findRoom"))
            ).click()
        except:
            self._showTrace("加载房间/区域失败 !")
            return False
        # room
        if not self.__selectRoom(reserve_info["room"]):
            return False
        else:
            have_hover_on_page = True
        # seat selections
        if not self.__selectSeat(reserve_info["seat_id"]):
            pass
        elif not self.__selectSeatTime(
            begin_time=reserve_info["begin_time"],
            end_time=reserve_info["end_time"],
            expct_duration=reserve_info["expect_duration"],
            satisfy_duration=reserve_info["satisfy_duration"]
        ):
            pass
        else:
            try:
                WebDriverWait(self.__driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "reserveBtn"))
                ).click()
                submit_reserve = True
                if not self._waitResponseLoad():
                    raise
                reserve_success = True
            except:
                self._showTrace(f"预约提交失败 !")
        if not submit_reserve and have_hover_on_page:
            self.__driver.refresh()
        return reserve_success