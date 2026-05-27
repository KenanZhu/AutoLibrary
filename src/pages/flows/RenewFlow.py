# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from selenium.common.exceptions import (
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.remote.webdriver import WebDriver

from base.MsgBase import MsgBase
from pages.MainShell import MainShell
from pages.components.RenewDialog import RenewDialog
from pages.flows._helpers import timeStrToMins, minsToTimeStr
from pages.strategies.TimeSelectMaker import TimeSelectMaker


class RenewFlow(MsgBase):

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

    def _validateRenewTime(
        self,
        end_time: str,
        target_renew_mins: int,
    ) -> bool:

        if target_renew_mins > self.LIBRARY_CLOSE_MINS:
            actual_renew_duration = self.LIBRARY_CLOSE_MINS - timeStrToMins(end_time)
            if actual_renew_duration <= 0:
                self._showTrace(
                    f"当前结束时间 {end_time} 已接近闭馆时间,无法续约 !", self.TraceLevel.ERROR
                )
                return False
            self._showTrace(
                f"续约时间已调整至闭馆时间 "
                f"{minsToTimeStr(self.LIBRARY_CLOSE_MINS)},"
                f"实际续约时长为 "
                f"{actual_renew_duration // 60} 小时 "
                f"{actual_renew_duration % 60} 分钟"
            )
        return True

    def execute(
        self,
        username: str,
        record: dict,
        renew_info: dict,
    ) -> bool:

        max_diff = renew_info.get("max_diff", 30)
        prefer_earlier = renew_info.get("prefer_early", True)
        end_time = record["time"]["end"]
        target_renew_mins = timeStrToMins(end_time) + renew_info.get("expect_duration", 2) * 60
        if not self._validateRenewTime(end_time, target_renew_mins):
            return False
        if not self._shell.waitExtendButton():
            self._showTrace(f"用户 {username} 续约界面加载失败 !", self.TraceLevel.ERROR)
            return False
        if self._shell.isExtendButtonDisabled():
            self._showTrace(
                f"用户 {username} 续约按钮不可用, 可能不在场馆内, "
                f"请连接图书馆网络后重试"
            )
            return False
        self._shell.clickExtendButton()
        try:
            with RenewDialog(self._driver) as dialog:
                if not dialog.waitUntilReady():
                    result_msg = dialog.getResultMessage()
                    self._showTrace(
                        f"\n"
                        f"      续约失败 !\n"
                        f"          {result_msg}"
                    )
                    self._shell.refresh()
                    self._showTrace(f"用户 {username} 续约失败 !", self.TraceLevel.ERROR)
                    return False
                result = dialog.selectBestTime(
                    target_renew_mins,
                    max_diff,
                    prefer_earlier,
                )
                if result.selected_index >= 0:
                    abs_diff = abs(result.actual_diff)
                    if result.actual_diff < 0:
                        relation = f"早了 {abs_diff} 分钟"
                    elif result.actual_diff > 0:
                        relation = f"晚了 {abs_diff} 分钟"
                    else:
                        relation = "正好等于 续约时间"
                    self._showTrace(
                        f"选择距离期望续约时间最近的 {result.display_text}, "
                        f"与期望续约时间相比 {relation}"
                    )
                    record["time"]["end"] = result.display_text.strip()
                    dialog.clickOk()
                    self._shell.refresh()
                    return True
                if not result.free_times:
                    self._showTrace("当前未查询到可用续约时间 !", self.TraceLevel.WARNING)
                else:
                    self._showTrace(
                        "无法选择最近的可用续约时间 ! "
                        f"所有可选时间与目标时间相差都超过了 {max_diff} 分钟 !",
                        self.TraceLevel.WARNING,
                    )
                    self._showTrace(f"当前可供续约的时间有: {result.free_times}")
                self._shell.refresh()
                return False
        except (NoSuchElementException, TimeoutException, ElementNotInteractableException) as e:
            self._showTrace(f"用户 {username} 续约失败 ! : {e}", self.TraceLevel.ERROR)
            self._shell.refresh()
            return False
