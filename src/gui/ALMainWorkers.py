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
    Signal, QThread
)

from operators.AutoLib import AutoLib
from utils.ConfigReader import ConfigReader


class AutoLibWorker(QThread):

    finishedSignal = Signal()
    showTraceSignal = Signal(str)
    showMsgSignal = Signal(str)

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict
    ):

        super().__init__()

        self.__input_queue = input_queue
        self.__output_queue = output_queue
        self.__config_paths = config_paths


    def checkTimeAvailable(
        self,
    ) -> bool:

        current_time = time.strftime("%H:%M", time.localtime())
        if current_time >= "23:30" or current_time <= "07:30":
            return False
        return True


    def checkConfigPaths(
        self,
    ) -> bool:

        if not all(
            os.path.exists(path) for path in self.__config_paths.values()
        ):
            self.showTraceSignal.emit(
                "配置文件路径不存在, 请检查配置文件路径是否正确。"
            )
            return False
        return True


    def loadConfigs(
        self
    ) -> bool:

        self.showTraceSignal.emit(
            f"正在加载配置文件, 运行配置文件路径: {self.__config_paths["run"]}"
        )
        self.__run_config = ConfigReader(
            self.__config_paths["run"]
        ).getConfigs()
        self.showTraceSignal.emit(
            f"正在加载配置文件, 用户配置文件路径: {self.__config_paths["user"]}"
        )
        self.__user_config = ConfigReader(
            self.__config_paths["user"]
        ).getConfigs()
        if self.__run_config is None or self.__user_config is None:
            self.showTraceSignal.emit(
                "配置文件加载失败, 请检查配置文件是否正确。"
            )
            return False
        if not self.__user_config.get("groups"):
            self.showTraceSignal.emit(
                "用户配置文件中无有效任务组, 请检查用户配置文件是否正确"
            )
            return False
        return True


    def run(
        self
    ):

        auto_lib = None
        try:
            if not self.checkTimeAvailable():
                self.showTraceSignal.emit(
                    "当前时间不在图书馆开放时间内\n"\
                    "    请在 07:30 - 23:30 之间尝试"
                )
                return
            if not self.checkConfigPaths():
                return
            self.showTraceSignal.emit("AutoLibrary 开始运行")
            if not self.loadConfigs():
                return
            auto_lib = AutoLib(
                self.__input_queue,
                self.__output_queue,
                self.__run_config
            )
            if auto_lib is None:
                self.showTraceSignal.emit(
                    "AutoLibrary 初始化失败"
                )
                return
            groups = self.__user_config.get("groups")
            for group in groups:
                time.sleep(0.2) # wait for the message queue to be empty
                if not group["enabled"]:
                    self.showTraceSignal.emit(
                        f"任务组 {group["name"]} 已跳过"
                    )
                    continue
                self.showTraceSignal.emit(
                    f"正在运行任务组 {group["name"]}"
                )
                auto_lib.run(
                    { "users": group.get("users", []) }
                )
        except Exception as e:
            self.showTraceSignal.emit(
                f"AutoLibrary 运行时发生异常 : {e}"
            )
        finally:
            if auto_lib:
                auto_lib.close()
                time.sleep(0.2) # wait for the message queue to be empty
            self.showTraceSignal.emit("AutoLibrary 运行结束")
            self.finishedSignal.emit()


class TimerTaskWorker(AutoLibWorker):

    finishedSignal_TimerWorker = Signal(dict)

    def __init__(
        self,
        timer_task: dict,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict
    ):

        super().__init__(input_queue, output_queue, config_paths)

        self.__timer_task = timer_task

    def run(
        self
    ):

        self.showTraceSignal.emit(
            f"定时任务 {self.__timer_task['name']} 开始运行"
        )
        super().run()
        self.showTraceSignal.emit(
            f"定时任务 {self.__timer_task['name']} 运行结束"
        )
        self.finishedSignal_TimerWorker.emit(self.__timer_task)