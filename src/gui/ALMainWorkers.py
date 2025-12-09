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


    def run(
        self
    ):

        auto_lib = None
        try:
            if not self.checkTimeAvailable():
                self.showTraceSignal.emit(
                    "当前时间不在图书馆开放时间内。\n"\
                    "    请在 07:30 - 23:30 之间尝试"
                )
                return
            if not self.checkConfigPaths():
                return
            self.showTraceSignal.emit("AutoLibrary 开始运行")
            auto_lib = AutoLib(
                self.__input_queue,
                self.__output_queue,
            )
            auto_lib.run(
                ConfigReader(self.__config_paths["system"]),
                ConfigReader(self.__config_paths["users"]),
            )
        except Exception as e:
            self.showTraceSignal.emit(
                f"AutoLibrary 运行时发生异常 : {e}"
            )
        finally:
            if auto_lib:
                auto_lib.close()
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

        super().__init__(
            input_queue,
            output_queue,
            config_paths,
        )

        self.__timer_task = timer_task
        self.__stopped = False

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