# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import sys
import time
import queue

from enum import Enum
from datetime import datetime, timedelta

from PySide6.QtCore import (
    Qt, Signal, Slot, QTimer
)
from PySide6.QtWidgets import (
    QDialog, QWidget, QListWidgetItem, QMessageBox,
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtGui import (
    QCloseEvent
)

from gui.Ui_ALTimerTaskWidget import Ui_ALTimerTaskWidget
from gui.ALAddTimerTaskDialog import ALAddTimerTaskWidget, TimerTaskStatus


class TimerTaskItemWidget(QWidget):

    def __init__(
        self,
        parent = None,
        timer_task: dict = None
    ):

        super().__init__(parent)

        self.__timer_task = timer_task
        self.modifyUi()


    def modifyUi(
        self
    ):

        self.ItemWidgetLayout = QHBoxLayout(self)
        self.ItemWidgetLayout.setSpacing(10)
        self.ItemWidgetLayout.setContentsMargins(10, 5, 10, 5)

        self.TaskInfoLayout = QVBoxLayout()
        self.TaskInfoLayout.setSpacing(5)
        TaskNameLabel = QLabel(self.__timer_task["name"])
        TaskNameLabelFont = TaskNameLabel.font()
        TaskNameLabelFont.setBold(True)
        TaskNameLabel.setFont(TaskNameLabelFont)
        TaskNameLabel.setFixedHeight(25)
        self.TaskInfoLayout.addWidget(TaskNameLabel)

        ExecuteTimeStr = self.__timer_task["execute_time"].strftime("%Y-%m-%d %H:%M:%S")
        ExecuteTimeLabel = QLabel(f"执行时间: {ExecuteTimeStr}")
        ExecuteTimeLabel.setStyleSheet("color: gray;")
        ExecuteTimeLabel.setFixedHeight(20)
        self.TaskInfoLayout.addWidget(ExecuteTimeLabel)

        self.ItemWidgetLayout.addLayout(self.TaskInfoLayout)
        self.ItemWidgetLayout.addStretch()

        match self.__timer_task["status"]:
            case TimerTaskStatus.PENDING:
                TaskStatusText = "等待中"
                TaskStatusColor = "#FF9800"
            case TimerTaskStatus.READY:
                TaskStatusText = "已就绪"
                TaskStatusColor = "#316BFF"
            case TimerTaskStatus.RUNNING:
                TaskStatusText = "执行中"
                TaskStatusColor = "#2294FF"
            case TimerTaskStatus.EXECUTED:
                TaskStatusText = "已执行"
                TaskStatusColor = "#4CAF50"
            case TimerTaskStatus.OUTDATED:
                TaskStatusText = "已过期"
                TaskStatusColor = "#FF5722"
        TaskStatusLabel = QLabel(TaskStatusText)
        TaskStatusLabel.setStyleSheet(f"""
            QLabel {{
                background-color: {TaskStatusColor};
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        TaskStatusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        TaskStatusLabel.setFixedSize(80, 25)
        self.ItemWidgetLayout.addWidget(TaskStatusLabel)

        TaskModeText = "静默" if self.__timer_task["silent"] else "显示"
        TaskModeColor = "#6325FF" if self.__timer_task["silent"] else "#2294FF"
        TaskModeLabel = QLabel(TaskModeText)
        TaskModeLabel.setStyleSheet(f"""
            QLabel {{
                background-color: {TaskModeColor};
                color: white;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        TaskModeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        TaskModeLabel.setFixedSize(60, 25)
        self.ItemWidgetLayout.addWidget(TaskModeLabel)

        self.DeleteButton = QPushButton("删除")
        self.DeleteButton.setFixedSize(80, 25)
        self.ItemWidgetLayout.addWidget(self.DeleteButton)
        if self.__timer_task["status"] == TimerTaskStatus.READY\
        or self.__timer_task["status"] == TimerTaskStatus.RUNNING:
            self.DeleteButton.setEnabled(False)
        self.setFixedHeight(55)


class ALTimerTaskWidget(QWidget, Ui_ALTimerTaskWidget):

    timerTasksChanged = Signal(list)
    timerTaskReady = Signal(dict)
    timerTaskWidgetClosed = Signal()

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)

        self.__timer_tasks = []
        self.__check_timer = None
        self.setupUi(self)
        self.connectSignals()
        self.setupTimer()


    def setupTimer(
        self
    ):

        self.__check_timer = QTimer(self)
        self.__check_timer.timeout.connect(self.checkTasks)
        self.__check_timer.start(500)


    def connectSignals(
        self
    ):

        self.AddTimerTaskButton.clicked.connect(self.addTask)
        self.ClearAllTimerTasksButton.clicked.connect(self.clearAllTasks)


    def closeEvent(
        self,
        event: QCloseEvent
    ):

        self.hide()
        self.timerTaskWidgetClosed.emit()
        event.ignore()


    def updateStat(
        self
    ):

        pending = 0
        in_queue = 0
        executed = 0
        total = len(self.__timer_tasks)
        for timer_task in self.__timer_tasks:
            if timer_task["status"] == TimerTaskStatus.PENDING:
                pending += 1
            elif timer_task["status"] == TimerTaskStatus.READY\
            or timer_task["status"] == TimerTaskStatus.RUNNING:
                in_queue += 1
            elif timer_task["status"] == TimerTaskStatus.EXECUTED:
                executed += 1
        self.TotalTaskLabel.setText(f"总任务：{total}")
        self.PendingTaskLabel.setText(f"待执行：{pending}")
        self.InQueueTaskLabel.setText(f"队列中：{in_queue}")
        self.ExecutedTaskLabel.setText(f"已执行：{executed}")


    def updateTimerTaskList(
        self
    ):

        self.TimerTasksListWidget.clear()
        self.__timer_tasks.sort(
            key = lambda x: x["execute_time"]
        )
        for timer_task in self.__timer_tasks:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, timer_task)
            widget = TimerTaskItemWidget(self, timer_task)
            widget.DeleteButton.clicked.connect(
                lambda _, uuid = timer_task["task_uuid"]: self.deleteTask(uuid)
            )
            item.setSizeHint(widget.size())
            self.TimerTasksListWidget.addItem(item)
            self.TimerTasksListWidget.setItemWidget(item, widget)


    def addTask(
        self
    ):

        dialog = ALAddTimerTaskWidget(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            timer_task = dialog.getTimerTask()
            self.__timer_tasks.append(timer_task)
            self.updateTimerTaskList()
            self.updateStat()


    def deleteTask(
        self,
        task_uuid: str
    ):

        self.__timer_tasks = [
            x for x in self.__timer_tasks
            if x["task_uuid"] != task_uuid
        ]
        self.updateTimerTaskList()
        self.updateStat()


    def clearAllTasks(
        self
    ):

        if not self.__timer_tasks:
            return
        result = QMessageBox.question(
            self,
            "确认 - AutoLibrary",
            "是否要清除所有定时任务 ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if result is QMessageBox.StandardButton.No:
            return
        in_queue_tasks = [
            x for x in self.__timer_tasks
            if x["status"] == TimerTaskStatus.READY
            or x["status"] == TimerTaskStatus.RUNNING
        ]
        in_queue_count = len(in_queue_tasks)
        if in_queue_count > 0:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                "存在正在执行或已就绪的队列任务，无法清除所有定时任务 !"
            )
        self.__timer_tasks = in_queue_tasks
        self.updateTimerTaskList()
        self.updateStat()


    def checkTasks(
        self
    ):

        now = datetime.now()
        for timer_task in self.__timer_tasks:
            if timer_task["execute_time"] > now:
                continue
            if timer_task["status"] is not TimerTaskStatus.PENDING:
                continue
            if timer_task["execute_time"] <= now + timedelta(seconds = -5):
                timer_task["status"] = TimerTaskStatus.OUTDATED
            else:
                timer_task["status"] = TimerTaskStatus.READY
                self.timerTaskReady.emit(timer_task)
        self.updateTimerTaskList()
        self.updateStat()


    @Slot(dict)
    def onTimerTaskIsRunning(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["task_uuid"] == timer_task["task_uuid"]:
                task["status"] = TimerTaskStatus.RUNNING
        self.updateTimerTaskList()
        self.updateStat()


    @Slot(dict)
    def onTimerTaskIsExecuted(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["task_uuid"] == timer_task["task_uuid"]:
                task["status"] = TimerTaskStatus.EXECUTED
        self.updateTimerTaskList()
        self.updateStat()
