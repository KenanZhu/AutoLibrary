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
from pages.components.CheckinResultDialog import CheckinResultDialog


class CheckinFlow(MsgBase):

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
        username: str,
    ) -> bool:

        if not self._shell.waitCheckinButton():
            self._showTrace(f"用户 {username} 签到界面加载失败 !", self.TraceLevel.ERROR)
            return False
        if self._shell.isCheckinButtonDisabled():
            self._showTrace("签到按钮不可用, 可能不在场馆内, 正在尝试启用......")
            if not self._shell.enableCheckinButtonByJS():
                self._showTrace(f"签到按钮启用失败 !", self.TraceLevel.ERROR)
                return False
            self._showTrace("签到按钮已启用")
        self._shell.clickCheckinButton()
        try:
            with CheckinResultDialog(self._driver) as dialog:
                result_msg = dialog.getResultMessage()
                if "签到成功" in result_msg:
                    details = dialog.getDetails()
                    if details:
                        if len(details) >= 5:
                            self._showTrace(
                                f"\n"
                                f"      签到成功 !\n"
                                f"          {details[1]}\n"
                                f"          {details[2]}\n"
                                f"          {details[3]}\n"
                                f"          {details[4]}"
                            )
                    else:
                        self._showTrace(
                            "\n"
                            "      签到成功 !\n"
                            "          未获取到签到详情 !"
                        )
                    dialog.clickOk()
                    self._showTrace(f"用户 {username} 签到成功 !")
                    return True
                else:
                    failure_reason = result_msg.replace("签到失败", "").strip()
                    self._showTrace(
                        f"\n"
                        "      签到失败 !\n"
                        f"          {failure_reason}"
                    )
                    dialog.clickOk()
                    self._showTrace(f"用户 {username} 签到失败 !", self.TraceLevel.ERROR)
                    return False
        except (TimeoutException, NoSuchElementException, ElementNotInteractableException):
            self._showTrace("签到时发生未知错误 !", self.TraceLevel.ERROR)
            return False
