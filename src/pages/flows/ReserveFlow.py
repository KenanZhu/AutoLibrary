# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue
from dataclasses import dataclass
from typing import Optional

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.remote.webdriver import WebDriver

from base.MsgBase import MsgBase
from pages.MainShell import MainShell
from pages.flows._helpers import timeStrToMins, minsToTimeStr
from pages.strategies.timeSelectMaker import TimeSelectMaker
from pages.ReserveView import ReserveView
from pages.components.ReserveResultDialog import ReserveResultDialog
from pages.components.TimeSelectDialog import TimeSelectDialog


@dataclass
class ReserveContext:

    username: str
    date: str
    floor: str
    room: str
    seat_id: str
    begin_time: str
    end_time: str
    begin_max_diff: int = 30
    end_max_diff: int = 30
    begin_prefer_early: bool = True
    end_prefer_early: bool = False
    expect_duration: int = 4
    satisfy_duration: bool = True


class ReserveFlow(MsgBase):

    LIBRARY_CLOSE_MINS = TimeSelectMaker.LIBRARY_CLOSE_MINS

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver: WebDriver,
        shell: MainShell,
    ) -> None:

        super().__init__(input_queue, output_queue)
        self._driver: WebDriver = driver
        self._shell: MainShell = shell
        self._ctx: Optional[ReserveContext] = None

    def execute(
        self,
        ctx: ReserveContext,
    ) -> bool:

        self._ctx = ctx
        submit_reserve = False
        reserve_success = False
        have_hover_on_page = False

        try:
            view = self._shell.gotoReserveView()
        except (NoSuchElementException, TimeoutException) as e:
            self._showTrace(f"加载预约选座页面失败 ! : {e}", self.TraceLevel.ERROR)
            return False
        except Exception as e:
            self._showTrace(f"加载预约选座页面失败 ! : {e}", self.TraceLevel.ERROR)
            return False
        if not view.selectDate(ctx.date):
            self._showTrace(f"选择日期失败 ! : {ctx.date} 不可用", self.TraceLevel.ERROR)
            return False
        self._showTrace(f"日期 {ctx.date} 选择成功 !")
        if not view.selectPlace("1"):
            self._showTrace("选择预约场所失败 ! : 图书馆 不可用", self.TraceLevel.ERROR)
            return False
        self._showTrace("预约场所 图书馆 选择成功 !")
        if not view.selectFloor(ctx.floor):
            display_floor = ReserveView.FLOOR_MAP.get(ctx.floor, ctx.floor)
            self._showTrace(f"选择楼层失败 ! : {display_floor} 不可用", self.TraceLevel.ERROR)
            return False
        self._showTrace(f"楼层 {ReserveView.FLOOR_MAP.get(ctx.floor)} 选择成功 !")
        if not view.selectRoom(ctx.room):
            display_room = ReserveView.ROOM_MAP.get(ctx.room, ctx.room)
            self._showTrace(f"选择房间失败 ! : {display_room} 不可用", self.TraceLevel.ERROR)
            return False
        self._showTrace(f"房间 {ReserveView.ROOM_MAP.get(ctx.room)} 选择成功 !")
        have_hover_on_page = True
        seat_map = view.openSeatMap()
        seat_status = seat_map.selectSeat(ctx.seat_id)
        if seat_status is None:
            self._showTrace(
                f"座位 {ctx.seat_id} 在该楼层区域中不存在, 请检查座位号是否正确",
                self.TraceLevel.WARNING,
            )
        else:
            self._showTrace(f"座位 {ctx.seat_id} 选择成功 ! : 当前状态 - '{seat_status}'")
            time_dialog = TimeSelectDialog(self._driver)
            select_time_ok = self._selectSeatTime(time_dialog)
            if not select_time_ok:
                self._showTrace("选择时间失败 !", self.TraceLevel.ERROR)
            else:
                try:
                    view.submitReserve()
                    submit_reserve = True
                    with ReserveResultDialog(self._driver) as result:
                        if result.isFailure():
                            self._showTrace("预约失败", self.TraceLevel.ERROR)
                        elif result.isSuccess():
                            details = result.getDetailTexts()
                            if len(details) >= 6:
                                self._showTrace(
                                    f"\n"
                                    f"      预约成功 !\n"
                                    f"          {details[1]}\n"
                                    f"          {details[2]}\n"
                                    f"          {details[3]}\n"
                                    f"          签到时间 ：{details[5]}"
                                )
                            else:
                                self._showTrace(
                                    "\n"
                                    "      预约成功 !\n"
                                    "          未找获取到详细信息"
                                )
                            reserve_success = True
                        else:
                            self._showTrace("预约结果加载失败 !", self.TraceLevel.ERROR)
                except (TimeoutException, ElementNotInteractableException):
                    self._showTrace("预约提交失败 !", self.TraceLevel.ERROR)
                except Exception:
                    self._showTrace("预约提交失败 !", self.TraceLevel.ERROR)
        if not submit_reserve and have_hover_on_page:
            view.refresh()
        if reserve_success:
            self._showTrace(f"用户 {ctx.username} 预约成功 !")
        else:
            self._showTrace(f"用户 {ctx.username} 预约失败 !", self.TraceLevel.ERROR)
        return reserve_success

    def _selectSeatTime(
        self,
        time_dialog: TimeSelectDialog,
    ) -> bool:

        ctx = self._ctx
        exp_beg_tm_str = ctx.begin_time
        exp_end_tm_str = ctx.end_time
        exp_beg_mins = timeStrToMins(exp_beg_tm_str)
        exp_end_mins = timeStrToMins(exp_end_tm_str)
        act_beg_mins = exp_beg_mins
        act_beg_tm_str = exp_beg_tm_str
        act_end_mins = exp_end_mins
        act_end_tm_str = exp_end_tm_str
        act_beg_mins = self._selectNearestTime(
            time_dialog,
            time_id="startTime",
            time_type="开始时间",
            target_time=exp_beg_mins,
            max_time_diff=ctx.begin_max_diff,
            prefer_earlier=ctx.begin_prefer_early,
        )
        if act_beg_mins == -1:
            return False
        act_beg_tm_str = minsToTimeStr(act_beg_mins)
        if ctx.satisfy_duration:
            exp_end_mins = self._calcEndTime(act_beg_mins, ctx.expect_duration)
            exp_end_tm_str = minsToTimeStr(exp_end_mins)
            self._showTrace(
                f"需要满足期望预约持续时间: {ctx.expect_duration} 小时, "
                f"根据开始时间 {act_beg_tm_str} 计算结束时间: {exp_end_tm_str}"
            )
        act_end_mins = self._selectNearestTime(
            time_dialog,
            time_id="endTime",
            time_type="结束时间",
            target_time=exp_end_mins,
            max_time_diff=ctx.end_max_diff,
            prefer_earlier=ctx.end_prefer_early,
        )
        if act_end_mins == -1:
            return False
        act_end_tm_str = minsToTimeStr(act_end_mins)
        self._showTrace(
            f"期望预约时间段: {exp_beg_tm_str} - {exp_end_tm_str}, "
            f"实际预约时间段: {act_beg_tm_str} - {act_end_tm_str}"
        )
        return True

    def _selectNearestTime(
        self,
        time_dialog: TimeSelectDialog,
        time_id: str,
        time_type: str,
        target_time: int,
        max_time_diff: int,
        prefer_earlier: bool,
    ) -> int:

        all_time_opts = time_dialog.getTimeOptions(time_id)
        if not all_time_opts:
            self._showTrace(
                f"{time_type} 选择失败 ! : 当前未查询到可用时间", self.TraceLevel.ERROR
            )
            return -1
        result = TimeSelectMaker.forReserve().decide(
            all_time_opts,
            target_time,
            max_time_diff,
            prefer_earlier
        )
        if result.selected_index >= 0:
            all_time_opts[result.selected_index].click()
            abs_diff = abs(result.actual_diff)
            if result.actual_diff < 0:
                relation = f"早了 {abs_diff} 分钟"
            elif result.actual_diff > 0:
                relation = f"晚了 {abs_diff} 分钟"
            else:
                relation = f"正好等于 {time_type}"
            self._showTrace(
                f"选择距离期望 {time_type} 最近的 {result.display_text}, "
                f"与期望 {time_type} 相比 {relation}"
            )
            return target_time + result.actual_diff
        target_time_str = minsToTimeStr(target_time)
        self._showTrace(
            f"无法选择最近的 {time_type} {target_time_str}, "
            f"所有可选时间与目标时间相差都超过 {max_time_diff} 分钟",
            self.TraceLevel.WARNING,
        )
        self._showTrace(f"当前可供预约的 {time_type} 有: {result.free_times}")
        return -1

    def _calcEndTime(
        self,
        begin_mins: int,
        duration: int,
    ) -> int:

        expect_end_mins = int(begin_mins + duration*60)
        if expect_end_mins > self.LIBRARY_CLOSE_MINS:
            expect_end_mins = self.LIBRARY_CLOSE_MINS
            self._showTrace(
                f"预约持续时间 {duration} 小时, 超过最大预约时间 23:30, "
                f"自动调整为 23:30",
                self.TraceLevel.WARNING,
            )
        return expect_end_mins
