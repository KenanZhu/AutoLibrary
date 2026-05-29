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

from selenium.common.exceptions import (
    ElementNotInteractableException,
    TimeoutException,
)
from selenium.webdriver.remote.webdriver import WebDriver

from base.MsgBase import MsgBase
from pages.MainShell import MainShell
from pages.strategies.TimeSelectMaker import TimeSelectMaker
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

    def execute(
        self,
        ctx: ReserveContext,
    ) -> bool:

        submit_reserve = False
        reserve_success = False
        have_hover_on_page = False

        try:
            view = self._shell.gotoReserveView()
        except (TimeoutException, ElementNotInteractableException) as e:
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
        seat_map = view.selectRoom(ctx.room)
        if seat_map is None:
            display_room = ReserveView.ROOM_MAP.get(ctx.room, ctx.room)
            self._showTrace(f"选择房间失败 ! : {display_room} 不可用", self.TraceLevel.ERROR)
            return False
        self._showTrace(f"房间 {ReserveView.ROOM_MAP.get(ctx.room)} 选择成功 !")
        have_hover_on_page = True
        seat_status = seat_map.selectSeat(ctx.seat_id)
        if seat_status is None:
            self._showTrace(
                f"座位 {ctx.seat_id} 在该楼层区域中不存在, 请检查座位号是否正确",
                self.TraceLevel.WARNING,
            )
        else:
            self._showTrace(f"座位 {ctx.seat_id} 选择成功 ! : 当前状态 - '{seat_status}'")
            try:
                time_dialog = TimeSelectDialog(self._driver, tracer=self._showTrace)
            except TimeoutException:
                self._showTrace("时间选择面板未出现 !", self.TraceLevel.ERROR)
            else:
                if not time_dialog.selectSeatTime(ctx):
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
        if not submit_reserve and have_hover_on_page:
            view.refresh()
        if reserve_success:
            self._showTrace(f"用户 {ctx.username} 预约成功 !")
        else:
            self._showTrace(f"用户 {ctx.username} 预约失败 !", self.TraceLevel.ERROR)
        return reserve_success
