# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue
import time

from base.MsgBase import MsgBase
from pages.ReserveView import ReserveView
from pages.flows._helpers import timeStrToMins, minsToTimeStr
from pages.strategies.TimeSelectMaker import TimeSelectMaker


class ReserveChecker(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
    ) -> None:

        super().__init__(input_queue, output_queue)

    def _containRequiredInfo(
        self,
        reserve_info: dict,
    ) -> bool:

        floor_map = ReserveView.FLOOR_MAP
        room_map = ReserveView.ROOM_MAP
        try:
            if reserve_info.get("floor") is None:
                raise ValueError("未指定楼层")
            if reserve_info["floor"] not in floor_map:
                raise ValueError(f"该楼层 '{reserve_info["floor"]}' 不存在")
            if reserve_info.get("room") is None:
                raise ValueError("未指定房间")
            if reserve_info["room"] not in room_map:
                raise ValueError(f"该房间 '{reserve_info["room"]}' 不存在")
            if reserve_info.get("seat_id") is None:
                raise ValueError("未指定座位")
            if reserve_info["seat_id"] == "":
                raise ValueError("未指定座位号")
            return True
        except ValueError as e:
            msg = (
                f"预约信息错误 ! : {e}, "
                f"由于缺少必要的预约信息, 无法开始预约流程"
            )
            self._showTrace(msg, self.TraceLevel.ERROR)
            self._showTrace(
                f"预约信息错误 ! : {e}, "
                f"由于缺少必要的预约信息, 无法开始预约流程, 请检查预约信息是否完整",
                20,
                no_log=True,
            )
            return False

    def _isValidDate(
        self,
        reserve_info: dict,
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
                    f"预约日期错误 ! :"
                    f"{reserve_info["date"]} 早于当前日期 {cur_date_str}, 自动设置为当前日期",
                    self.TraceLevel.WARNING,
                )
                reserve_info["date"] = cur_date_str
        return True

    def _isValidBeginTime(
        self,
        reserve_info: dict,
    ) -> bool:

        cur_time = time.strftime("%H:%M", time.localtime())
        cur_date = time.strftime("%Y-%m-%d", time.localtime())
        if reserve_info.get("begin_time") is None:
            reserve_info["begin_time"] = {}
        if "time" not in reserve_info["begin_time"]:
            reserve_info["begin_time"]["time"] = cur_time
            self._showTrace(f"开始时间未指定, 自动设置为当前时间: {cur_time}")
        elif reserve_info.get("date") == cur_date:
            begin_mins = timeStrToMins(reserve_info["begin_time"]["time"])
            cur_mins = timeStrToMins(cur_time)
            if begin_mins < cur_mins:
                self._showTrace(
                    f"开始时间 {reserve_info['begin_time']['time']} 已过当前时间 {cur_time}, "
                    f"自动调整为当前时间",
                    self.TraceLevel.WARNING,
                )
                reserve_info["begin_time"]["time"] = cur_time
        if "max_diff" not in reserve_info["begin_time"]:
            reserve_info["begin_time"]["max_diff"] = 30
            self._showTrace("开始时间最大时间差未指定, 自动设置为 30 分钟")
        if "prefer_early" not in reserve_info["begin_time"]:
            reserve_info["begin_time"]["prefer_early"] = True
            self._showTrace("是否优先选择更早开始时间未指定, 自动设置为 True")
        return True

    def _isValidExpectDuration(
        self,
        reserve_info: dict,
    ) -> bool:

        if reserve_info.get("satisfy_duration") is None:
            reserve_info["satisfy_duration"] = True
            self._showTrace("预约满足时长要求未指定, 默认满足")
        if reserve_info["satisfy_duration"]:
            if reserve_info.get("expect_duration") is None:
                reserve_info["expect_duration"] = 4
                self._showTrace("需要满足预约持续时间, 但未指定, 使用默认时长为 4 小时")
        return True

    def _isValidEndTime(
        self,
        reserve_info: dict,
    ) -> bool:

        if reserve_info.get("end_time") is None:
            reserve_info["end_time"] = {}
        if "time" not in reserve_info["end_time"]:
            end_mins = timeStrToMins(reserve_info["begin_time"]["time"])
            end_mins = end_mins + int(reserve_info["expect_duration"] * 60)
            reserve_info["end_time"] = {
                "time": minsToTimeStr(end_mins),
                "max_diff": 30,
                "prefer_early": False,
            }
            self._showTrace(
                f"结束时间未指定, 自动设置为开始时间加上期望时长: "
                f"{reserve_info["end_time"]["time"]}"
            )
        if "max_diff" not in reserve_info["end_time"]:
            reserve_info["end_time"]["max_diff"] = 30
            self._showTrace("结束时间最大时间差未指定, 自动设置为 30 分钟")
        if "prefer_early" not in reserve_info["end_time"]:
            reserve_info["end_time"]["prefer_early"] = False
            self._showTrace("是否优先选择较晚结束时间未指定, 自动设置为 True")
        return True

    def _finalCheck(
        self,
        reserve_info: dict,
    ) -> bool:

        begin_time = reserve_info["begin_time"]
        end_time = reserve_info["end_time"]
        begin_mins = timeStrToMins(begin_time["time"])
        end_mins = timeStrToMins(end_time["time"])
        if end_mins < begin_mins and reserve_info["satisfy_duration"] is False:
            self._showTrace(
                f"结束时间 {end_time["time"]} 早于开始时间 {begin_time["time"]}, "
                f"尝试交换时间",
                self.TraceLevel.WARNING,
            )
            reserve_info["end_time"], reserve_info["begin_time"] = begin_time, end_time
            begin_time, end_time = end_time, begin_time
            begin_mins = timeStrToMins(begin_time["time"])
            end_mins = timeStrToMins(end_time["time"])
        max_end_mins = TimeSelectMaker.LIBRARY_CLOSE_MINS
        if end_mins > max_end_mins:
            close_time_str = minsToTimeStr(TimeSelectMaker.LIBRARY_CLOSE_MINS)
            self._showTrace(
                f"结束时间 {end_time["time"]} 晚于 {close_time_str}, "
                f"自动设置为 {close_time_str}",
                self.TraceLevel.WARNING,
            )
            reserve_info["end_time"]["time"] = close_time_str
            end_mins = max_end_mins
        if reserve_info["satisfy_duration"]:
            if reserve_info["expect_duration"] > 8:
                self._showTrace(
                    f"该用户设置了优先满足时长要求, 但是预约期望持续时间 "
                    f"{reserve_info["expect_duration"]} 小时 "
                    f"超出最大时长 8 小时, 自动设置为 8 小时",
                    self.TraceLevel.WARNING,
                )
                reserve_info["expect_duration"] = 8
        else:
            if end_mins - begin_mins > 8*60:
                self._showTrace(
                    f"该用户未设置优先满足时长要求, 但是检查到预约持续时间 "
                    f"{float((end_mins - begin_mins) / 60)} 小时 "
                    f"超出最大时长 8 小时, 自动设置为 8 小时",
                    self.TraceLevel.WARNING,
                )
                reserve_info["end_time"]["time"] = minsToTimeStr(begin_mins + 8*60)
        return True

    def check(
        self,
        reserve_info: dict,
    ) -> bool:

        if not self._containRequiredInfo(reserve_info):
            return False
        if not self._isValidDate(reserve_info):
            return False
        if not self._isValidBeginTime(reserve_info):
            return False
        if not self._isValidExpectDuration(reserve_info):
            return False
        if not self._isValidEndTime(reserve_info):
            return False
        if not self._finalCheck(reserve_info):
            return False
        self._showTrace(
            f"预约信息检查完成, 准备预约 "
            f"{reserve_info["date"]} "
            f"{reserve_info["begin_time"]["time"]} - "
            f"{reserve_info["end_time"]["time"]} "
            f"图书馆 "
            f"{ReserveView.FLOOR_MAP[reserve_info["floor"]]} "
            f"{ReserveView.ROOM_MAP[reserve_info["room"]]} "
            f"的座位 {reserve_info["seat_id"]}"
        )
        return True