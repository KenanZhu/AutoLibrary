# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from PySide6.QtCore import (
    QObject,
    QTimer,
    Signal,
    Slot
)

from gui.ALMainWorker import TimerTaskWorker


class ALTimerTaskPoller(QObject):

    taskRunning = Signal(dict)
    taskFinished = Signal(bool, dict)
    taskExecuted = Signal(dict)
    taskError = Signal(dict)

    def __init__(
        self,
        parent=None,
        input_queue: queue.Queue = None,
        output_queue: queue.Queue = None,
        config_paths: list = None
    ):

        super().__init__(parent)
        self.__input_queue = input_queue or queue.Queue()
        self.__output_queue = output_queue or queue.Queue()
        self.__config_paths = config_paths or []
        self.__task_queue = queue.Queue()
        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__poll)
        self.__worker = None
        self.__stopped = False

    def start(
        self
    ):

        self.__stopped = False
        self.__timer.start(500)

    def stop(
        self
    ):

        self.__stopped = True
        self.__timer.stop()
        self.__cleanupWorker()

    def enqueue(
        self,
        task: dict
    ):

        self.__task_queue.put(task)

    def isRunning(
        self
    ) -> bool:

        return self.__worker is not None

    def updateConfigPaths(
        self,
        config_paths: list
    ):

        self.__config_paths = config_paths

    @Slot()
    def __poll(
        self
    ):

        if self.__worker is not None:
            return
        try:
            task = self.__task_queue.get_nowait()
            self.__timer.stop()
            self.taskRunning.emit(task)
            self.__worker = TimerTaskWorker(
                task,
                self.__input_queue,
                self.__output_queue,
                self.__config_paths
            )
            self.__worker.timerTaskWorkerIsFinished.connect(self.__onFinished)
            self.__worker.start()
        except queue.Empty:
            pass

    @Slot(bool, dict)
    def __onFinished(
        self,
        is_error: bool,
        task: dict
    ):

        self.__worker.timerTaskWorkerIsFinished.disconnect(self.__onFinished)
        self.__worker.wait(1000)
        self.__worker.deleteLater()
        self.__worker = None
        task["executed"] = True
        self.taskFinished.emit(is_error, task)
        if not is_error:
            self.taskExecuted.emit(task)
        else:
            self.taskError.emit(task)
        if not self.__stopped:
            self.__timer.start(500)

    def __cleanupWorker(
        self
    ):

        if self.__worker is None:
            return
        try:
            self.__worker.timerTaskWorkerIsFinished.disconnect(self.__onFinished)
        except (TypeError, RuntimeError):
            pass
        self.__worker.wait(2000)
        self.__worker.deleteLater()
        self.__worker = None
