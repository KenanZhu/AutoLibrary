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
import copy
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
    QCloseEvent, QScreen
)

from gui.Ui_ALTimerTaskWidget import Ui_ALTimerTaskWidget
from gui.ALAddTimerTaskDialog import ALAddTimerTaskWidget, TimerTaskStatus

from utils.ConfigReader import ConfigReader
from utils.ConfigWriter import ConfigWriter


class SortPolicy(Enum):

    BY_NAME = "按名称"
    BY_ADD_TIME = "按添加时间"
    BY_EXECUTE_TIME = "按执行时间"


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
            case TimerTaskStatus.ERROR:
                TaskStatusText = "执行失败"
                TaskStatusColor = "#FF5722"
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

    timerTasksChanged = Signal()
    timerTaskIsReady = Signal(dict)
    timerTaskWidgetClosed = Signal()

    def __init__(
        self,
        parent = None,
        timer_tasks_config_path: str = ""
    ):

        super().__init__(parent)

        self.__timer_tasks = []
        self.__check_timer = None
        self.__sort_policy = SortPolicy.BY_EXECUTE_TIME
        self.__sort_order = Qt.SortOrder.AscendingOrder
        self.__timer_tasks_config_path = timer_tasks_config_path

        self.setupUi(self)
        self.connectSignals()
        self.setupTimer()
        if not self.initializeTimerTasks():
            return


    def connectSignals(
        self
    ):

        self.AddTimerTaskButton.clicked.connect(self.addTask)
        self.ClearAllTimerTasksButton.clicked.connect(self.clearAllTasks)
        self.TimerTaskSortTypeComboBox.currentIndexChanged.connect(self.onSortPolicyComboBoxChanged)
        self.TimerTaskSortOrderToggleButton.clicked.connect(self.onSortOrderToggleButtonClicked)
        self.timerTasksChanged.connect(self.onTimerTasksChanged)


    def setupTimer(
        self
    ):

        self.__check_timer = QTimer(self)
        self.__check_timer.timeout.connect(self.checkTasks)
        self.__check_timer.start(500)


    def initializeTimerTasks(
        self
    ) -> bool:

        timer_tasks = self.loadTimerTasks(self.__timer_tasks_config_path)
        if timer_tasks is not None:
            self.__timer_tasks = timer_tasks
            self.timerTasksChanged.emit()
            return True
        timer_tasks = []
        if self.saveTimerTasks(self.__timer_tasks_config_path, copy.deepcopy(timer_tasks)):
            QMessageBox.information(
                self,
                "信息 - AutoLibrary",
                f"定时任务配置文件初始化完成: \n{self.__timer_tasks_config_path}"
            )
            self.__timer_tasks = timer_tasks
            self.updateTimerTaskList()
            return True
        return False


    def loadTimerTasks(
        self,
        timer_tasks_config_path: str
    ) -> list:

        try:
            if not timer_tasks_config_path or not os.path.exists(timer_tasks_config_path):
                raise Exception("定时任务配置文件不存在")
            timer_tasks = ConfigReader(timer_tasks_config_path).getConfigs()
            if timer_tasks and "timer_tasks" in timer_tasks:
                for task in timer_tasks["timer_tasks"]:
                    task["add_time"] = datetime.strptime(task["add_time"], "%Y-%m-%d %H:%M:%S")
                    task["execute_time"] = datetime.strptime(task["execute_time"], "%Y-%m-%d %H:%M:%S")
                    task["status"] = TimerTaskStatus(task["status"])
                return timer_tasks["timer_tasks"]
            raise Exception("定时任务配置文件格式错误")
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"加载定时任务配置发生错误 ! : {e}\n"\
                f"文件路径: {timer_tasks_config_path}"
            )
            return None


    def saveTimerTasks(
        self,
        timer_tasks_config_path: str,
        timer_tasks: list
    ) -> bool:

        try:
            if not timer_tasks_config_path:
                raise Exception("配置文件路径为空")
            for task in timer_tasks:
                task["add_time"] = task["add_time"].strftime("%Y-%m-%d %H:%M:%S")
                task["execute_time"] = task["execute_time"].strftime("%Y-%m-%d %H:%M:%S")
                task["status"] = task["status"].value
            ConfigWriter(
                timer_tasks_config_path,
                { "timer_tasks": timer_tasks }
            )
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"保存定时任务配置发生错误 ! : {e}\n"\
                f"文件路径: {timer_tasks_config_path}"
            )
            return False


    def showEvent(
        self,
        event
    ):

        result = super().showEvent(event)

        screen_rect = self.screen().geometry()
        target_pos = self.parent().geometry().center()
        target_pos.setX(target_pos.x() - self.width()//2)
        target_pos.setY(target_pos.y() - self.height()//2)
        if target_pos.x() < 0:
            target_pos.setX(0)
        if target_pos.x() + self.width() > screen_rect.width():
            target_pos.setX(screen_rect.width() - self.width())
        if target_pos.y() < 0:
            target_pos.setY(0)
        if target_pos.y() + self.height() > screen_rect.height():
            target_pos.setY(screen_rect.height() - self.height())
        self.move(target_pos)

        return result


    def closeEvent(
        self,
        event: QCloseEvent
    ):

        self.hide()
        self.timerTaskWidgetClosed.emit()
        event.ignore()


    def sortTimerTasks(
        self,
        policy: SortPolicy = SortPolicy.BY_EXECUTE_TIME,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ):

        if policy == SortPolicy.BY_NAME:
            self.__timer_tasks.sort(
                key = lambda x: x["name"],
                reverse = order is Qt.SortOrder.DescendingOrder
            )
        elif policy == SortPolicy.BY_ADD_TIME:
            self.__timer_tasks.sort(
                key = lambda x: x["add_time"],
                reverse = order is Qt.SortOrder.DescendingOrder
            )
        elif policy == SortPolicy.BY_EXECUTE_TIME:
            self.__timer_tasks.sort(
                key = lambda x: x["execute_time"],
                reverse = order is Qt.SortOrder.DescendingOrder
            )


    def updateStat(
        self
    ):

        pending = 0
        in_queue = 0
        executed = 0
        invalid = 0
        total = len(self.__timer_tasks)
        for timer_task in self.__timer_tasks:
            if timer_task["status"] == TimerTaskStatus.PENDING:
                pending += 1
            elif timer_task["status"] == TimerTaskStatus.READY\
            or timer_task["status"] == TimerTaskStatus.RUNNING:
                in_queue += 1
            elif timer_task["status"] == TimerTaskStatus.EXECUTED:
                executed += 1
            elif timer_task["status"] == TimerTaskStatus.ERROR\
            or timer_task["status"] == TimerTaskStatus.OUTDATED:
                invalid += 1
        self.TotalTaskLabel.setText(f"总任务：{total}")
        self.PendingTaskLabel.setText(f"待执行：{pending}")
        self.InQueueTaskLabel.setText(f"队列中：{in_queue}")
        self.ExecutedTaskLabel.setText(f"已执行：{executed}")
        self.InvalidTaskLabel.setText(f"无效的：{invalid}")


    def updateTimerTaskList(
        self
    ):

        self.TimerTasksListWidget.clear()
        self.sortTimerTasks(self.__sort_policy, self.__sort_order)
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
            self.timerTasksChanged.emit()


    def deleteTask(
        self,
        task_uuid: str
    ):

        self.__timer_tasks = [
            x for x in self.__timer_tasks
            if x["task_uuid"] != task_uuid
        ]
        self.timerTasksChanged.emit()


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
        self.timerTasksChanged.emit()


    def checkTasks(
        self
    ):

        need_update = False

        now = datetime.now()
        for timer_task in self.__timer_tasks:
            if timer_task["execute_time"] > now:
                continue
            if timer_task["status"] is not TimerTaskStatus.PENDING:
                continue
            if timer_task["execute_time"] <= now + timedelta(seconds = -5):
                timer_task["status"] = TimerTaskStatus.OUTDATED
                need_update = True
            else:
                timer_task["status"] = TimerTaskStatus.READY
                self.timerTaskIsReady.emit(timer_task)
                need_update = True
        if need_update:
            self.timerTasksChanged.emit()

    @Slot(int)
    def onSortPolicyComboBoxChanged(
        self,
        policy: int
    ):

        mapping = {
            0: SortPolicy.BY_NAME,
            1: SortPolicy.BY_ADD_TIME,
            2: SortPolicy.BY_EXECUTE_TIME
        }
        self.__sort_policy = mapping[policy]
        self.updateTimerTaskList()

    @Slot()
    def onSortOrderToggleButtonClicked(
        self
    ):

        self.__sort_order = Qt.SortOrder.AscendingOrder\
            if self.__sort_order is Qt.SortOrder.DescendingOrder\
            else Qt.SortOrder.DescendingOrder
        self.TimerTaskSortOrderToggleButton.setText(
            "↑" if self.__sort_order is Qt.SortOrder.AscendingOrder else "↓"
        )
        self.updateTimerTaskList()

    @Slot()
    def onTimerTasksChanged(
        self
    ):

        self.saveTimerTasks(self.__timer_tasks_config_path, copy.deepcopy(self.__timer_tasks))
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
        self.timerTasksChanged.emit()


    @Slot(dict)
    def onTimerTaskIsExecuted(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["task_uuid"] == timer_task["task_uuid"]:
                task["status"] = TimerTaskStatus.EXECUTED
        self.timerTasksChanged.emit()

    @Slot(dict)
    def onTimerTaskIsError(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["task_uuid"] == timer_task["task_uuid"]:
                task["status"] = TimerTaskStatus.ERROR
        self.timerTasksChanged.emit()
