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
    Slot, Signal, QThread
)

from base.MsgBase import MsgBase
from operators.AutoLib import AutoLib
from utils.ConfigReader import ConfigReader


class AutoLibWorker(QThread, MsgBase):

    finishedSignal = Signal()
    finishedWithErrorSignal = Signal()

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict
    ):

        super().__init__(input_queue = input_queue, output_queue = output_queue)

        self.__config_paths = config_paths


    def checkTimeAvailable(
        self,
    ) -> bool:

        current_time = time.strftime("%H:%M", time.localtime())
        if current_time >= "23:30" or current_time <= "07:30":
            self._showTrace(
                "当前时间不在图书馆开放时间内, 请在 07:30 - 23:30 之间尝试"
            )
            return False
        return True


    def checkConfigPaths(
        self,
    ) -> bool:

        if not all(
            os.path.exists(path) for path in self.__config_paths.values()
        ):
            self._showTrace("配置文件路径不存在, 请检查配置文件路径是否正确")
            return False
        return True


    def loadConfigs(
        self
    ) -> bool:

        self._showTrace(
            f"正在加载配置文件, 运行配置文件路径: {self.__config_paths["run"]}"
        )
        self.__run_config = ConfigReader(
            self.__config_paths["run"]
        ).getConfigs()
        self._showTrace(
            f"正在加载配置文件, 用户配置文件路径: {self.__config_paths["user"]}"
        )
        self.__user_config = ConfigReader(
            self.__config_paths["user"]
        ).getConfigs()
        if self.__run_config is None or self.__user_config is None:
            self._showTrace("配置文件加载失败, 请检查配置文件是否正确")
            self._showTrace("配置文件加载失败, 请检查配置文件是否正确")
            return False
        if not self.__user_config.get("groups"):
            self._showTrace(
                "用户配置文件中无有效任务组, 请检查用户配置文件是否正确"
            )
            return False
        return True


    def run(
        self
    ):

        auto_lib = None
        self._showTrace("AutoLibrary 开始运行")
        if not self.checkTimeAvailable()\
        or not self.checkConfigPaths():
            # time or config existence check failed, skip and finish
            pass
        else:
            try:
                if not self.loadConfigs():
                    raise Exception("配置文件加载失败")
                auto_lib = AutoLib(
                    self._input_queue,
                    self._output_queue,
                    self.__run_config
                )
                groups = self.__user_config.get("groups")
                for group in groups:
                    if not group["enabled"]:
                        self._showTrace(f"任务组 {group["name"]} 已跳过")
                        continue
                    self._showTrace(f"正在运行任务组 {group["name"]}")
                    auto_lib.run(
                        { "users": group.get("users", []) }
                    )
            except Exception as e:
                self._showTrace(f"AutoLibrary 运行时发生异常 : {e}")
                self.finishedWithErrorSignal.emit()
                return
        if auto_lib:
            auto_lib.close()
        self._showTrace("AutoLibrary 运行结束")
        self.finishedSignal.emit()


class TimerTaskWorker(AutoLibWorker):

    finishedSignal_TimerWorker = Signal(bool, dict)

    def __init__(
        self,
        timer_task: dict,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict
    ):

        super().__init__(input_queue, output_queue, config_paths)

        self.__timer_task = timer_task
        self.finishedSignal.connect(self.onTimerTaskIsFinished)
        self.finishedWithErrorSignal.connect(self.onTimerTaskIsError)

    def run(
        self
    ):

        self._showTrace(f"定时任务 {self.__timer_task['name']} 开始运行")
        super().run()

    @Slot(dict)
    def onTimerTaskIsError(
        self
    ):

        self._showTrace(f"定时任务 {self.__timer_task['name']} 运行时发生异常")
        self.finishedSignal_TimerWorker.emit(True, self.__timer_task)

    @Slot(dict)
    def onTimerTaskIsFinished(
        self
    ):

        self._showTrace(f"定时任务 {self.__timer_task['name']} 运行结束")
        self.finishedSignal_TimerWorker.emit(False, self.__timer_task)
