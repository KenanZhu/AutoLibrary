# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import time
import queue

from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.LibTimeSelector import LibTimeSelector


class LibReserve(LibTimeSelector):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver: WebDriver
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
            "2": "二层西区",
            "3": "三层内环",
            "4": "三层外环",
            "5": "四层内环",
            "6": "四层外环",
            "7": "四层期刊",
            "8": "五层考研"
        }


    def _waitResponseLoad(
        self,
    ) -> bool:

        try:
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.CLASS_NAME, "layoutSeat"))
            )
            title_elements = []
            # reserve failed without title elements, so we need to try
            try:
                WebDriverWait(self.__driver, 2).until(
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
                    self._showTrace(f"\n"\
                        f"      预约成功 !\n"\
                        f"          {contents[1]}\n"\
                        f"          {contents[2]}\n"\
                        f"          {contents[3]}\n"\
                        f"          签到时间 ：{contents[5]}"
                    )
                else:
                    self._showTrace("\n"\
                        "      预约成功 !\n"\
                        "          未找获取到详细信息"
                    )
            return True
        except:
            self._showTrace(f"预约结果加载失败 !")
            return False


    def __containRequiredInfo(
        self,
        reserve_info: dict
    ) -> bool:

        try:
            # must contain the required infomation
            # key 'place' is no need to check
            # because 'place' is only has one possible value '1' or '图书馆'
            if reserve_info.get("floor") is None: # if existence ?
                raise ValueError("未指定楼层")
            if reserve_info["floor"] not in self.__floor_map: # if in the mao ?
                raise ValueError(f"该楼层 '{reserve_info['floor']}' 不存在")
            if reserve_info.get("room") is None:
                raise ValueError("未指定房间")
            if reserve_info["room"] not in self.__room_map:
                raise ValueError(f"该房间 '{reserve_info['room']}' 不存在")
            if reserve_info.get("seat_id") is None:
                raise ValueError("未指定座位")
            if reserve_info["seat_id"] == "":
                raise ValueError("未指定座位号")
            return True
        except ValueError as e:
            self._showTrace(
                f"预约信息错误 ! : {e}, "\
                f"由于缺少必要的预约信息, 无法开始预约流程, 请检查预约信息是否完整"
            )
            return False


    def __isValidDate(
        self,
        reserve_info: dict
    ) -> bool:

        cur_date_str = time.strftime("%Y-%m-%d", time.localtime())
        cur_timestamp = time.mktime(time.strptime(cur_date_str, "%Y-%m-%d"))
        if reserve_info.get("date") is None:
            reserve_info["date"] = cur_date_str
            self._showTrace(f"预约日期未指定, 自动设置为当前日期: {cur_date_str}")
        else:
            res_timestamp = time.mktime(time.strptime(reserve_info["date"], "%Y-%m-%d"))
            if res_timestamp < cur_timestamp:
                self._showTrace(
                    f"预约日期错误 ! :"\
                    f"{reserve_info['date']} 早于当前日期 {cur_date_str}, 自动设置为当前日期"
                )
                reserve_info["date"] = cur_date_str
        return True


    def __isValidBeginTime(
        self,
        reserve_info: dict
    ) -> bool:

        cur_time = time.strftime("%H:%M", time.localtime())
        if reserve_info.get("begin_time") is None:
            reserve_info["begin_time"] = {}
        if "time" not in reserve_info["begin_time"]:
            reserve_info["begin_time"]["time"] = cur_time
            self._showTrace(f"开始时间未指定, 自动设置为当前时间: {cur_time}")
        if "max_diff" not in reserve_info["begin_time"]:
            reserve_info["begin_time"]["max_diff"] = 30
            self._showTrace(f"开始时间最大时间差未指定, 自动设置为 30 分钟")
        if "prefer_early" not in reserve_info["begin_time"]:
            reserve_info["begin_time"]["prefer_early"] = True
            self._showTrace(f"是否优先选择更早开始时间未指定, 自动设置为 True")
        return True


    def __isValidExpectDuration(
        self,
        reserve_info: dict
    ) -> bool:

        if reserve_info.get("satisfy_duration") is None:
            reserve_info["satisfy_duration"] = True
            self._showTrace("预约满足时长要求未指定, 默认满足")
        if reserve_info["satisfy_duration"]:
            if reserve_info.get("expect_duration") is None:
                reserve_info["expect_duration"] = 4
                self._showTrace("需要满足预约持续时间, 但未指定, 使用默认时长为 4 小时")
        return True


    def __isValidEndTime(
        self,
        reserve_info: dict
    ) -> bool:

        if reserve_info.get("end_time") is None:
            reserve_info["end_time"] = {}
        if "time" not in reserve_info["end_time"]:
            # here we add the expect duration to the begin time first,
            # the edge case that the end time is later than 23:30 will
            # be handled in __finalCheck. so no need to concern about it.
            end_mins = self._timeStrToMins(reserve_info["begin_time"]["time"])
            end_mins = end_mins + int(reserve_info["expect_duration"]*60)
            reserve_info["end_time"] = {
                "time": self._minsToTimeStr(end_mins),
                "max_diff": 30,
                "prefer_early": False
            }
            self._showTrace(
                f"结束时间未指定, 自动设置为开始时间加上期望时长: {reserve_info['end_time']['time']}"
            )
        if "max_diff" not in reserve_info["end_time"]:
            reserve_info["end_time"]["max_diff"] = 30
            self._showTrace(f"结束时间最大时间差未指定, 自动设置为 30 分钟")
        if "prefer_early" not in reserve_info["end_time"]:
            reserve_info["end_time"]["prefer_early"] = False
            self._showTrace(f"是否优先选择较晚结束时间未指定, 自动设置为 True")
        return True


    def __finalCheck(
        self,
        reserve_info: dict
    ):

        begin_time, end_time = reserve_info["begin_time"], reserve_info["end_time"]
        begin_mins = self._timeStrToMins(begin_time["time"])
        end_mins = self._timeStrToMins(end_time["time"])

        # if end time is earlier than begin_time, exchange them
        # except that the user has set the satisfy_duration to True
        if end_mins < begin_mins and reserve_info["satisfy_duration"] is False:
            self._showTrace(
                f"结束时间 {end_time['time']} 早于开始时间 {begin_time['time']}, 尝试交换时间"
            )
            reserve_info["end_time"], reserve_info["begin_time"] = begin_time, end_time
            begin_time, end_time = end_time, begin_time
            begin_mins = self._timeStrToMins(begin_time["time"])
            end_mins = self._timeStrToMins(end_time["time"])

        # ensure the end time is not later than 23:30
        max_end_mins = self._timeStrToMins("23:30")
        if end_mins > max_end_mins:
            self._showTrace(
                f"结束时间 {end_time['time']} 晚于 23:30, 自动设置为 23:30"
            )
            reserve_info["end_time"]["time"] = "23:30"
            end_mins = max_end_mins

        # ensure the duration is not longer than 8 hours
        if reserve_info["satisfy_duration"]:
            if reserve_info["expect_duration"] > 8:
                self._showTrace(
                    f"该用户设置了优先满足时长要求, 但是预约期望持续时间 "
                    f"{reserve_info['expect_duration']} 小时 "
                    f"超出最大时长 8 小时, 自动设置为 8 小时"
                )
                reserve_info["expect_duration"] = 8
        else:
            if end_mins - begin_mins > 8*60:
                self._showTrace(
                    f"该用户未设置优先满足时长要求, 但是检查到预约持续时间 "
                    f"{float((end_mins - begin_mins)/60)} 小时 "
                    f"超出最大时长 8 小时, 自动设置为 8 小时"
                )
                reserve_info["end_time"]["time"] = self._minsToTimeStr(begin_mins + 8*60)
        return True


    def __checkReserveInfo(
        self,
        reserve_info: dict
    ) -> bool:

        if not self.__containRequiredInfo(reserve_info):
            return False
        if not self.__isValidDate(reserve_info):
            return False
        if not self.__isValidBeginTime(reserve_info):
            return False
        if not self.__isValidExpectDuration(reserve_info):
            return False
        if not self.__isValidEndTime(reserve_info):
            return False
        if not self.__finalCheck(reserve_info):
            return False
        self._showTrace(
            f"预约信息检查完成, 准备预约 "
            f"{reserve_info['date']} "
            f"{reserve_info['begin_time']['time']} - "
            f"{reserve_info['end_time']['time']} "
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
        option_locator: tuple = None
    ) -> bool:

        try:
            # click the trigger element
            WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable(trigger_locator)
            ).click()
            if option_locator:
                # select the option element if specified
                WebDriverWait(self.__driver, 2).until(
                    EC.element_to_be_clickable(option_locator)
                ).click()
            self._showTrace(success_msg)
            return True
        except:
            self._showTrace(fail_msg)
            return False


    def __clickElementByJS(
        self,
        trigger_locator_id: str,
        option_query_selector: str,
        fail_msg: str,
        success_msg: str,
    ) -> bool:

        script = f"""
        try {{
            var trigger = document.getElementById('{trigger_locator_id}');
            if (trigger) {{
                trigger.click();
                var option = document.querySelector("{option_query_selector}");
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
        result = self.__driver.execute_script(script)
        time.sleep(0.1)
        if result:
            self._showTrace(success_msg)
        else:
            self._showTrace(fail_msg)
        return result


    def __selectDate(
        self,
        date_str: str
    ) -> bool:

        if self.__clickElementByJS(
            trigger_locator_id="onDate_select",
            option_query_selector=f"p#options_onDate a[value='{date_str}']",
            success_msg=f"日期 {date_str} 选择成功 !",
            fail_msg=f"选择日期失败 ! : {date_str} 不可用"
        ):
            return True
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

        place = "1" # the library only have this place :)
        display_place = "图书馆"
        if self.__clickElementByJS(
            trigger_locator_id="display_building",
            option_query_selector=f"p#options_building a[value='{place}']",
            success_msg=f"预约场所 {display_place} 选择成功 !",
            fail_msg=f"选择预约场所失败 ! : {display_place} 不可用"
        ):
            return True
        return self.__clickElement(
            trigger_locator=(By.ID, "display_building"),
            option_locator=(By.XPATH, f"//p[@id='options_building']/a[@value='{place}']"),
            success_msg=f"预约场所 {display_place} 选择成功 !",
            fail_msg=f"选择预约场所失败 ! : {display_place} 不可用"
        )


    def __selectFloor(
        self,
        floor: str
    ) -> bool:

        display_floor = self.__floor_map.get(floor)
        if self.__clickElementByJS(
            trigger_locator_id="floor_select",
            option_query_selector=f"p#options_floor a[value='{floor}']",
            success_msg=f"楼层 {display_floor} 选择成功 !",
            fail_msg=f"选择楼层失败 ! : {display_floor} 不可用"
        ):
            return True
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
        # find room
        try:
            WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.ID, "findRoom"))
            ).click()
        except:
            self._showTrace("加载房间/区域失败 !")
            return False
        # select room
        try:
            WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.ID, f"room_{room}"))
            ).click()
            self._showTrace(f"房间 {display_room} 选择成功 !")
            return True
        except:
            self._showTrace(f"选择房间失败 ! : {display_room} 不可用")
            return False


    def __selectSeat(
        self,
        seat_id: str
    ) -> bool:

        try:
            # wait fot seat layout element to load
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.ID, "seatLayout"))
            )
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li[id^='seat_']"))
            )
        except:
            self._showTrace(f"座位加载失败 !")
            return False
        try:
            all_seats = self.__driver.find_elements(
                By.CSS_SELECTOR, "li[id^='seat_']"
            )
            seat_id_upper = seat_id.lstrip('0').upper()
            for seat in all_seats:
                if not seat_id_upper == seat.text.lstrip('0'):
                    continue
                seat_link = seat.find_element(By.TAG_NAME, "a")
                WebDriverWait(self.__driver, 2).until(
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

        """
            Select the nearest available time option.

            Returns:
                int: The actual selected time value in minutes.
        """
        # Wait for time options to load
        try:
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, f"#{time_id} ul li a")
                )
            )
        except:
            self._showTrace(f"{time_type} 选择失败 ! : 当前未查询到可用时间")
            return -1

        # Find best time option
        all_time_opts = self.__driver.find_elements(
            By.CSS_SELECTOR,
            f"#{time_id} ul li a"
        )
        if not all_time_opts:
            self._showTrace(f"{time_type} 选择失败 ! : 当前未查询到可用时间")
            return -1
        best_opt, best_text, actual_diff, free_times = self._findBestTimeOption(
            all_time_opts, target_time, max_time_diff, prefer_earlier, is_reserve=True
        )
        if best_opt is not None:
            best_opt.click()
            abs_diff = abs(actual_diff)
            time_relation = self._formatTimeRelation(abs_diff, actual_diff, time_type)
            target_time += actual_diff
            self._showTrace(
                f"选择距离期望 {time_type} 最近的 {best_text}, "
                f"与期望 {time_type} 相比 {time_relation}"
            )
            return target_time
        self._showTrace(
            f"无法选择最近的 {time_type} {self._minsToTimeStr(target_time)}, "
            f"所有可选时间与目标时间相差都超过 {max_time_diff} 分钟"
        )
        self._showTrace(f"当前可供预约的 {time_type} 有: {free_times}")
        return -1


    def __selectSeatTime(
        self,
        begin_time: dict,
        end_time: dict,
        expect_duration: int = 4,
        satisfy_duration: bool = True
    ) -> bool:

        """
            Select seat begin and end time.
        """
        exp_beg_tm_str = begin_time["time"]
        exp_end_tm_str = end_time["time"]
        # Initialize actual time strings for logging
        act_beg_tm_str = exp_beg_tm_str
        act_end_tm_str = exp_end_tm_str
        exp_beg_mins = self._timeStrToMins(exp_beg_tm_str)
        act_beg_mins = exp_beg_mins
        exp_end_mins = self._timeStrToMins(exp_end_tm_str)
        act_end_mins = exp_end_mins

        # Select begin time
        act_beg_mins = self.__selectNearestTime(
            time_id="startTime",
            time_type="开始时间",
            target_time=exp_beg_mins,
            max_time_diff=begin_time["max_diff"],
            prefer_earlier=begin_time["prefer_early"]
        )
        if act_beg_mins == -1:
            return False
        act_beg_tm_str = self._minsToTimeStr(act_beg_mins)

        # If 'satisfy_duration' is True, select end time based on actual begin time
        if satisfy_duration:
            exp_end_mins = int(self.validateAndAdjustEndTime(act_beg_mins, expect_duration))
            exp_end_tm_str = self._minsToTimeStr(exp_end_mins)
            self._showTrace(
                f"需要满足期望预约持续时间: {expect_duration} 小时, "
                f"根据开始时间 {act_beg_tm_str} 计算结束时间: {exp_end_tm_str}"
            )

        # Select end time
        act_end_mins = self.__selectNearestTime(
            time_id="endTime",
            time_type="结束时间",
            target_time=exp_end_mins,
            max_time_diff=end_time["max_diff"],
            prefer_earlier=end_time["prefer_early"]
        )
        if act_end_mins == -1:
            return False
        act_end_tm_str = self._minsToTimeStr(act_end_mins)
        self._showTrace(
            f"期望预约时间段: {exp_beg_tm_str} - {exp_end_tm_str}, "
            f"实际预约时间段: {act_beg_tm_str} - {act_end_tm_str}"
        )
        return True


    def validateAndAdjustEndTime(
        self,
        begin_mins: int,
        duration: int
    ) -> int:

        """
            Validate and adjust reserve end time to library closing time if needed.
        """
        LIBRARY_CLOSE_TIME = self._timeStrToMins("23:30")
        expect_end_mins = int(begin_mins + duration*60)
        if expect_end_mins > LIBRARY_CLOSE_TIME:
            expect_end_mins = LIBRARY_CLOSE_TIME
            self._showTrace(
                f"预约持续时间 {duration} 小时, 超过最大预约时间 23:30, 自动调整为 23:30"
            )
        return expect_end_mins


    def reserve(
        self,
        username: str,
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
            WebDriverWait(self.__driver, 2).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='/map']"))
            ).click()
            WebDriverWait(self.__driver, 2).until(
                EC.presence_of_element_located((By.ID, "seatLayout"))
            )
        except:
            self._showTrace(f"加载预约选座页面失败 !")
            return False
        # date, place, floor, room
        if not self.__selectDate(reserve_info["date"]):
            return False
        if not self.__selectPlace(reserve_info["place"]):
            return False
        if not self.__selectFloor(reserve_info["floor"]):
            return False
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
            expect_duration=reserve_info["expect_duration"],
            satisfy_duration=reserve_info["satisfy_duration"]
        ):
            pass
        else:
            try:
                WebDriverWait(self.__driver, 2).until(
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
        if reserve_success:
            self._showTrace(f"用户 {username} 预约成功 !")
        else:
            self._showTrace(f"用户 {username} 预约失败 !")
        return reserve_success