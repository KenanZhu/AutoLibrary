# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import time
import queue

from PySide6.QtCore import (
    Signal,
    QThread,
)

from base.MsgBase import MsgBase
from pages.AutoLib import AutoLib
from utils.JSONReader import JSONReader
from autoscript import createEngine


class AutoLibWorker(MsgBase, QThread):

    autoLibWorkerIsFinished = Signal()
    autoLibWorkerFinishedWithError = Signal()

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict,
    ):

        MsgBase.__init__(self, input_queue, output_queue)
        QThread.__init__(self)
        self.__config_paths = config_paths

    def checkTimeAvailable(
        self,
    ) -> bool:

        current_time = time.strftime("%H:%M", time.localtime())
        if current_time >= "23:30" or current_time <= "07:30":
            self._showTrace(
                "当前时间不在图书馆开放时间内, 请在 07:30 - 23:30 之间尝试",
                self.TraceLevel.WARNING,
            )
            return False
        self._showLog(f"时间检查通过, 当前时间: {current_time}", self.TraceLevel.INFO)
        return True

    def checkConfigPaths(
        self,
    ) -> bool:

        if not all(
            os.path.exists(path) for path in self.__config_paths.values()
        ):
            self._showTrace(
                "配置文件路径不存在, 请检查配置文件路径是否正确",
                self.TraceLevel.ERROR,
            )
            return False
        self._showLog(
            f"配置文件路径检查通过, 路径: {self.__config_paths}",
            self.TraceLevel.INFO,
        )
        return True

    def loadConfigs(
        self,
    ) -> bool:

        self._showTrace(
            f"正在加载配置文件, 运行配置文件路径: {self.__config_paths["run"]}",
            no_log=True,
        )
        self._run_config = JSONReader(self.__config_paths["run"]).data()
        self._showTrace(
            f"正在加载配置文件, 用户配置文件路径: {self.__config_paths["user"]}",
            no_log=True,
        )
        self._user_config = JSONReader(self.__config_paths["user"]).data()
        if self._run_config is None or self._user_config is None:
            self._showTrace(
                "配置文件加载失败, 请检查配置文件是否正确",
                self.TraceLevel.ERROR,
            )
            return False
        if not self._user_config.get("groups"):
            self._showTrace(
                "用户配置文件中无有效任务组, 请检查用户配置文件是否正确",
                self.TraceLevel.WARNING,
            )
            return False
        self._showLog(
            f"配置文件加载成功, 任务组数量: {len(self._user_config.get("groups"))}",
            self.TraceLevel.INFO,
        )
        return True

    def _runName(
        self,
    ) -> str:

        return "常规任务"

    def _beforeCreateAutoLib(
        self,
    ):

        return

    def _onChecksFailed(
        self,
    ) -> bool:

        return True

    def _onFinished(
        self,
    ):

        self.autoLibWorkerIsFinished.emit()

    def _onError(
        self,
        error_msg: str,
    ):

        self._showTrace(error_msg, self.TraceLevel.ERROR)
        self.autoLibWorkerFinishedWithError.emit()

    def run(
        self,
    ):

        auto_lib = None
        self._showTrace(f"{self._runName()} 开始运行")

        if not self.checkTimeAvailable() or not self.checkConfigPaths():
            if not self._onChecksFailed():
                return
        else:
            try:
                if not self.loadConfigs():
                    raise Exception("配置文件加载失败")
                self._beforeCreateAutoLib()
                auto_lib = AutoLib(
                    self._input_queue,
                    self._output_queue,
                    self._run_config,
                )
                groups = self._user_config.get("groups")
                for group in groups:
                    if not group.get("enabled", False):
                        self._showTrace(f"任务组 {group.get("name", "未知")} 已跳过", no_log=True)
                        continue
                    self._showTrace(f"正在运行任务组 {group.get("name", "未知")}", no_log=True)
                    auto_lib.run({"users": group.get("users", [])})
            except Exception as e:
                self._onError(f"{self._runName()} 运行时发生异常 : {e}")
                return
        if auto_lib:
            auto_lib.close()
        self._showTrace(f"{self._runName()} 运行结束")
        self._onFinished()


class TimerTaskWorker(AutoLibWorker):

    timerTaskWorkerIsFinished = Signal(bool, dict)

    def __init__(
        self,
        timer_task: dict,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict,
    ):

        super().__init__(input_queue, output_queue, config_paths)
        self.__timer_task = timer_task

    def _runName(
        self,
    ) -> str:

        return f"定时任务 '{self.__timer_task.get("name", "未知")}'"

    def _beforeCreateAutoLib(
        self,
    ):

        self.applyRepeatAutoScript()

    def _onChecksFailed(
        self,
    ) -> bool:

        self._showTrace("定时任务跳过执行: 时间或配置文件检查未通过")
        self.timerTaskWorkerIsFinished.emit(False, self.__timer_task)
        return False

    def _onFinished(
        self,
    ):

        self.timerTaskWorkerIsFinished.emit(False, self.__timer_task)

    def _onError(
        self,
        error_msg: str,
    ):

        self._showTrace(error_msg, self.TraceLevel.ERROR)
        self.timerTaskWorkerIsFinished.emit(True, self.__timer_task)

    def applyRepeatAutoScript(
        self,
    ):

        auto_script = self.__timer_task.get("repeat_auto_script", "")
        if not auto_script or not auto_script.strip():
            return
        self._showTrace("检测到重复定时任务 AutoScript, 开始执行...", no_log=True)
        groups = self._user_config.get("groups", [])
        affected_count = 0
        for group in groups:
            if not group.get("enabled", False):
                continue
            for user in group.get("users", []):
                try:
                    engine = createEngine()
                    engine.execute(auto_script, user)
                    affected_count += 1
                except ValueError as e:
                    self._showTrace(
                        f"AutoScript 执行错误 (用户 {user.get("username", "未知")}): {e}",
                        self.TraceLevel.ERROR,
                    )
        self._showLog(
            f"AutoScript 执行完毕, 影响 {affected_count} 个用户",
            self.TraceLevel.INFO,
        )
