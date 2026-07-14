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
import copy

from enum import Enum
from datetime import datetime, timedelta

from PySide6.QtCore import (
    QTimer,
    Qt,
    Signal,
    Slot
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent
)
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget
)

import managers.config.ConfigManager as ConfigManager

from gui.ALTimerTaskAddDialog import (
    ALTimerTaskAddDialog,
    ALTimerTaskStatus
)
from gui.ALTimerTaskHistoryDialog import ALTimerTaskHistoryDialog
from gui.ALWidgetMixin import CenterOnParentMixin
from gui.resources.ui.Ui_ALTimerTaskManageWidget import Ui_ALTimerTaskManageWidget
from interfaces.ConfigProvider import (
    CfgKey,
    ConfigProvider
)
from utils.TimerUtils import TimerUtils


class ALTimerTaskItemWidget(QWidget):

    editRequested = Signal(dict)

    def __init__(
        self,
        parent = None,
        timer_task: dict = None
    ):

        super().__init__(parent)
        self.__timer_task = timer_task
        self.__manage_widget = parent

        self.modifyUi()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)

    def modifyUi(
        self
    ):

        self.ItemWidgetLayout = QHBoxLayout(self)
        self.ItemWidgetLayout.setSpacing(10)
        self.ItemWidgetLayout.setContentsMargins(10, 5, 10, 5)

        self.TaskInfoLayout = QVBoxLayout()
        self.TaskInfoLayout.setSpacing(5)
        TaskNameLabel = QLabel(self.__timer_task["name"])
        task_name_label_font = TaskNameLabel.font()
        task_name_label_font.setBold(True)
        TaskNameLabel.setFont(task_name_label_font)
        TaskNameLabel.setFixedHeight(25)
        self.TaskInfoLayout.addWidget(TaskNameLabel)
        execute_time_str = self.__timer_task["execute_time"].strftime("%Y-%m-%d %H:%M:%S")
        if self.__timer_task.get("repeat", False):
            repeat_days = self.__timer_task.get("repeat_days", [])
            repeat_hour = self.__timer_task.get("repeat_hour", 0)
            repeat_minute = self.__timer_task.get("repeat_minute", 0)
            repeat_second = self.__timer_task.get("repeat_second", 0)
            if len(repeat_days) == 7:
                time_str = f"{repeat_hour:02d}:{repeat_minute:02d}:{repeat_second:02d}"
                ExecuteTimeLabel = QLabel(f"下次执行时间: {execute_time_str} (每日 {time_str})")
            else:
                day_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
                selected_days = [day_names[d] for d in repeat_days]
                time_str = f"{repeat_hour:02d}:{repeat_minute:02d}:{repeat_second:02d}"
                ExecuteTimeLabel = QLabel(f"下次执行时间: {execute_time_str} (每{','.join(selected_days)} {time_str})")
        else:
            ExecuteTimeLabel = QLabel(f"执行时间: {execute_time_str}")
        ExecuteTimeLabel.setStyleSheet("color: #969696;")
        ExecuteTimeLabel.setFixedHeight(20)
        self.TaskInfoLayout.addWidget(ExecuteTimeLabel)
        self.ItemWidgetLayout.addLayout(self.TaskInfoLayout)
        self.ItemWidgetLayout.addStretch()

        match self.__timer_task["status"]:
            case ALTimerTaskStatus.PENDING:
                TaskStatusText = "等待中"
                TaskStatusColor = "#FF9800"
            case ALTimerTaskStatus.READY:
                TaskStatusText = "已就绪"
                TaskStatusColor = "#316BFF"
            case ALTimerTaskStatus.RUNNING:
                TaskStatusText = "执行中"
                TaskStatusColor = "#2294FF"
            case ALTimerTaskStatus.EXECUTED:
                TaskStatusText = "已执行"
                TaskStatusColor = "#4CAF50"
            case ALTimerTaskStatus.ERROR:
                TaskStatusText = "执行失败"
                TaskStatusColor = "#DC0000"
            case ALTimerTaskStatus.OUTDATED:
                TaskStatusText = "已过期"
                TaskStatusColor = "#DC0000"
        TaskStatusLabel = QLabel(TaskStatusText)
        TaskStatusLabel.setStyleSheet(f"""
            QLabel {{
                background-color: {TaskStatusColor};
                color: #FFFFFF;
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
                color: #FFFFFF;
                border-radius: 5px;
                font-weight: bold;
            }}
        """)
        TaskModeLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        TaskModeLabel.setFixedSize(60, 25)
        self.ItemWidgetLayout.addWidget(TaskModeLabel)

        if self.__timer_task.get("repeat", False):
            self.HistoryButton = QPushButton("历史")
            self.HistoryButton.setFixedSize(80, 25)
            self.ItemWidgetLayout.addWidget(self.HistoryButton)
        self.DeleteButton = QPushButton("删除")
        self.DeleteButton.setFixedSize(80, 25)
        self.DeleteButton.setStyleSheet("color: #DC0000;")
        self.ItemWidgetLayout.addWidget(self.DeleteButton)
        if self.__timer_task["status"] == ALTimerTaskStatus.READY\
        or self.__timer_task["status"] == ALTimerTaskStatus.RUNNING:
            self.DeleteButton.setEnabled(False)
        self.setFixedHeight(55)

    @Slot(object)
    def showContextMenu(
        self,
        pos
    ):

        Menu = QMenu(self)
        EditAction = QAction("编辑", self)
        EditAction.triggered.connect(
            lambda: self.editRequested.emit(self.__timer_task)
        )
        Menu.addAction(EditAction)
        if self.__timer_task["status"] != ALTimerTaskStatus.RUNNING\
        and self.__timer_task["status"] != ALTimerTaskStatus.READY:
            DeleteAction = QAction("删除", self)
            DeleteAction.triggered.connect(
                lambda: self.__manage_widget.deleteTask(self.__timer_task)
            )
            Menu.addAction(DeleteAction)
        Menu.exec(self.mapToGlobal(pos))


class ALTimerTaskManageWidget(CenterOnParentMixin, QWidget, Ui_ALTimerTaskManageWidget):

    class SortPolicy(Enum):

        BY_NAME = "按名称"
        BY_ADD_TIME = "按添加时间"
        BY_EXECUTE_TIME = "按执行时间"

    timerTaskIsReady = Signal(dict)
    timerTasksChanged = Signal()
    timerTaskManageWidgetIsClosed = Signal()

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self.__cfg_mgr: ConfigProvider = ConfigManager.instance()
        self.__timer_tasks = []
        self.__CheckTimer = None
        self.__sort_policy = self.SortPolicy.BY_EXECUTE_TIME
        self.__sort_order = Qt.SortOrder.AscendingOrder

        self.setupUi(self)
        self.connectSignals()
        self.setupTimer()
        if not self.initializeTimerTasks():
            raise Exception("定时任务配置文件初始化失败 !")

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

        self.__CheckTimer = QTimer(self)
        self.__CheckTimer.timeout.connect(self.checkTasks)
        self.__CheckTimer.start(500)

    def initializeTimerTasks(
        self
    ) -> bool:

        timer_tasks = self.getTimerTasks()
        if timer_tasks is not None:
            self.__timer_tasks = timer_tasks
            self.timerTasksChanged.emit()
            return True
        timer_tasks = []
        if self.setTimerTasks(copy.deepcopy(timer_tasks)):
            self.__timer_tasks = timer_tasks
            return True
        return False

    def getTimerTasks(
        self
    ) -> list:

        try:
            timer_tasks = self.__cfg_mgr.get(CfgKey.TIMERTASK.ROOT)
            if timer_tasks and "timer_tasks" in timer_tasks:
                for task in timer_tasks["timer_tasks"]:
                    task["added_time"] = datetime.strptime(task["added_time"], "%Y-%m-%d %H:%M:%S")
                    task["execute_time"] = datetime.strptime(task["execute_time"], "%Y-%m-%d %H:%M:%S")
                    task["status"] = ALTimerTaskStatus(task["status"])
                    if "repeat_history" in task:
                        for item in task["repeat_history"]:
                            item["result"] = ALTimerTaskStatus(item["result"])
                return timer_tasks["timer_tasks"]
            raise Exception("定时任务配置文件格式错误")
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"加载定时任务配置发生错误 ! : \n{e}"
            )
            return None

    def setTimerTasks(
        self,
        timer_tasks: list
    ) -> bool:

        try:
            for task in timer_tasks:
                task["added_time"] = task["added_time"].strftime("%Y-%m-%d %H:%M:%S")
                task["execute_time"] = task["execute_time"].strftime("%Y-%m-%d %H:%M:%S")
                task["status"] = task["status"].value
                if "repeat_history" in task:
                    for item in task["repeat_history"]:
                        item["result"] = item["result"].value
            self.__cfg_mgr.set(CfgKey.TIMERTASK.ROOT, { "timer_tasks": timer_tasks })
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"保存定时任务配置发生错误 ! : \n{e}"
            )
            return False

    def closeEvent(
        self,
        event: QCloseEvent
    ):

        self.hide()
        self.timerTaskManageWidgetIsClosed.emit()
        event.ignore()

    def sortTimerTasks(
        self,
        policy: SortPolicy = SortPolicy.BY_EXECUTE_TIME,
        order: Qt.SortOrder = Qt.SortOrder.AscendingOrder
    ):

        if policy == self.SortPolicy.BY_NAME:
            self.__timer_tasks.sort(
                key = lambda x: x["name"],
                reverse = order is Qt.SortOrder.DescendingOrder
            )
        elif policy == self.SortPolicy.BY_ADD_TIME:
            self.__timer_tasks.sort(
                key = lambda x: x["added_time"],
                reverse = order is Qt.SortOrder.DescendingOrder
            )
        elif policy == self.SortPolicy.BY_EXECUTE_TIME:
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
            if timer_task["status"] == ALTimerTaskStatus.PENDING:
                pending += 1
            elif timer_task["status"] == ALTimerTaskStatus.READY\
            or timer_task["status"] == ALTimerTaskStatus.RUNNING:
                in_queue += 1
            elif timer_task["status"] == ALTimerTaskStatus.EXECUTED:
                executed += 1
            elif timer_task["status"] == ALTimerTaskStatus.ERROR\
            or timer_task["status"] == ALTimerTaskStatus.OUTDATED:
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
            Item = QListWidgetItem()
            Item.setData(Qt.UserRole, timer_task)
            Widget = ALTimerTaskItemWidget(self, timer_task)
            Widget.DeleteButton.clicked.connect(
                lambda _, task = timer_task: self.deleteTask(task)
            )
            if timer_task.get("repeat", False) and hasattr(Widget, "HistoryButton"):
                Widget.HistoryButton.clicked.connect(
                    lambda _, task = timer_task: self.showTaskHistory(task)
                )
            Widget.editRequested.connect(self.editTask)
            Item.setSizeHint(Widget.size())
            self.TimerTasksListWidget.addItem(Item)
            self.TimerTasksListWidget.setItemWidget(Item, Widget)

    def addTask(
        self
    ):

        Dialog = ALTimerTaskAddDialog(self)
        if Dialog.exec() == QDialog.DialogCode.Accepted:
            timer_task = Dialog.getTimerTask()
            self.__timer_tasks.append(timer_task)
            self.timerTasksChanged.emit()

    def editTask(
        self,
        timer_task: dict
    ):

        Dialog = ALTimerTaskAddDialog(self, timer_task)
        if Dialog.exec() == QDialog.DialogCode.Accepted:
            updated = Dialog.getTimerTask()
            for i, task in enumerate(self.__timer_tasks):
                if task["uuid"] == updated["uuid"]:
                    self.__timer_tasks[i] = updated
                    break
            self.timerTasksChanged.emit()

    @staticmethod
    def getTimerTaskDetailMessage(
        timer_task: dict
    ):

        if "repeat_history" not in timer_task:
            history = []
        else:
            history = timer_task["repeat_history"]
        history_count = len(history)
        return (
            f"任务名称：{timer_task["name"]}\n"
            f"添加时间：{timer_task["added_time"]}\n"
            f"当前状态：{timer_task["status"].value}\n"
            f"下次执行时间：{datetime.strftime(timer_task["execute_time"], "%Y-%m-%d %H:%M:%S")}\n"
            f"已记录次数：{history_count}"
        )

    def deleteTask(
        self,
        timer_task: dict
    ):

        if timer_task["repeat"]: # when delete a repeat task
            MsgBox = QMessageBox(self)
            MsgBox.setIcon(QMessageBox.Icon.Question)
            MsgBox.setWindowTitle("警告 - AutoLibrary")
            MsgBox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            MsgBox.setText("删除可重复性任务将同时删除所有已执行的记录 !\n是否继续 ?")
            MsgBox.setDetailedText(
                "以下可重复性任务将被删除：\n"\
                "\n"
                f"{self.getTimerTaskDetailMessage(timer_task)}"
            )
            result = MsgBox.exec()
            if result != QMessageBox.StandardButton.Yes:
                return
        task_uuid = timer_task["uuid"]
        self.__timer_tasks = [
            x for x in self.__timer_tasks
            if x["uuid"] != task_uuid
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
        if result == QMessageBox.StandardButton.No:
            return
        # READY and RUNNING tasks cannot be cleared
        in_queue_tasks = [
            x for x in self.__timer_tasks
            if x["status"] == ALTimerTaskStatus.READY
            or x["status"] == ALTimerTaskStatus.RUNNING
        ]
        in_queue_count = len(in_queue_tasks)
        if in_queue_count > 0:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"存在 {in_queue_count} 个正在执行或已就绪的队列任务,无法清除所有定时任务 !"
            )
            return
        # repeat tasks ask before clear
        repeat_tasks = [
            x for x in self.__timer_tasks
            if x.get("repeat", False)
        ]
        repeat_tasks_count = len(repeat_tasks)
        if repeat_tasks_count > 0:
            MsgBox = QMessageBox(self)
            MsgBox.setIcon(QMessageBox.Icon.Question)
            MsgBox.setWindowTitle("警告 - AutoLibrary")
            MsgBox.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            MsgBox.setText(
                f"存在 {repeat_tasks_count} 个可重复性任务,\n"
                "删除可重复性任务将同时删除所有已执行的记录 !\n"
                "是否继续 ?"
            )
            delete_msgs = [
                self.getTimerTaskDetailMessage(x) for x in repeat_tasks
            ]
            MsgBox.setDetailedText(
                "以下可重复性任务将被删除：\n"\
                "\n"
                f"{"\n\n".join(delete_msgs)}"
            )
            result = MsgBox.exec()
            if result != QMessageBox.StandardButton.Yes:
                return
        # clear all tasks
        self.__timer_tasks.clear()
        self.timerTasksChanged.emit()

    def showTaskHistory(
        self,
        task: dict
    ):

        # Here we use reference to task data, not copy.
        # So any change of task data in history dialog will be
        # reflected in the timer task list
        # Thus we can emit timerTasksChanged signal to
        # update config file
        Dialog = ALTimerTaskHistoryDialog(self, task)
        if Dialog.exec() == QDialog.DialogCode.Accepted:
            self.timerTasksChanged.emit()

    def checkTasks(
        self
    ):

        need_update = False

        now = datetime.now()
        for timer_task in self.__timer_tasks:
            if timer_task["execute_time"] > now:
                continue
            if timer_task["status"] is not ALTimerTaskStatus.PENDING:
                continue
            if timer_task["execute_time"] <= now + timedelta(seconds = -5):
                if timer_task.get("repeat", False):
                    self.onRepeatTimerTaskIs(ALTimerTaskStatus.OUTDATED, timer_task)
                else:
                    timer_task["status"] = ALTimerTaskStatus.OUTDATED
                need_update = True
            else:
                timer_task["status"] = ALTimerTaskStatus.READY
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
            0: self.SortPolicy.BY_NAME,
            1: self.SortPolicy.BY_ADD_TIME,
            2: self.SortPolicy.BY_EXECUTE_TIME
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

        self.setTimerTasks(copy.deepcopy(self.__timer_tasks))
        self.updateTimerTaskList()
        self.updateStat()

    @Slot(dict)
    def onTimerTaskIsRunning(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["uuid"] == timer_task["uuid"]:
                task["status"] = ALTimerTaskStatus.RUNNING
                break
        self.timerTasksChanged.emit()

    def onRepeatTimerTaskIs(
        self,
        status: ALTimerTaskStatus,
        timer_task: dict
    ) -> dict:

        # only these status are valid
        valid_statuses = {ALTimerTaskStatus.EXECUTED, ALTimerTaskStatus.ERROR,
                         ALTimerTaskStatus.OUTDATED}
        if status not in valid_statuses:
            return timer_task
        if "repeat_history" not in timer_task:
            timer_task["repeat_history"] = []
        if status != ALTimerTaskStatus.OUTDATED:
            executed_time = datetime.now()
            duration = (executed_time - timer_task["execute_time"]).total_seconds()
            timer_task["repeat_history"].append({
                "execute_time": timer_task["execute_time"].strftime("%Y-%m-%d %H:%M:%S"),
                "executed_time": executed_time.strftime("%Y-%m-%d %H:%M:%S"),
                "result": status,
                "duration": duration,
                "uuid": timer_task["uuid"]
            })
        else:
            current_time = datetime.now()
            execute_time = timer_task["execute_time"]
            execute_weekday = execute_time.weekday()
            delta_days = (current_time - execute_time).days
            for i in range(delta_days + 1):
                if (execute_weekday + i)%7 in timer_task["repeat_days"]:
                    timer_task["repeat_history"].append({
                        "execute_time": (execute_time + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
                        "executed_time": (execute_time + timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S"),
                        "result": status,
                        "duration": 0,
                        "uuid": timer_task["uuid"]
                    })
        next_time = TimerUtils.getNextTimerRepeatTime(
            timer_task["repeat_days"],
            timer_task["repeat_hour"],
            timer_task["repeat_minute"],
            timer_task["repeat_second"]
        )
        if next_time:
            timer_task["execute_time"] = next_time
            timer_task["status"] = ALTimerTaskStatus.PENDING
            timer_task["executed"] = False
        else:
            timer_task["status"] = status
        return timer_task

    @Slot(dict)
    def onTimerTaskIsExecuted(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["uuid"] == timer_task["uuid"]:
                if task.get("repeat", False):
                    self.onRepeatTimerTaskIs(ALTimerTaskStatus.EXECUTED, task)
                else:
                    task["status"] = ALTimerTaskStatus.EXECUTED
                break
        self.timerTasksChanged.emit()

    @Slot(dict)
    def onTimerTaskIsError(
        self,
        timer_task: dict
    ):

        for task in self.__timer_tasks:
            if task["uuid"] == timer_task["uuid"]:
                if task.get("repeat", False):
                    self.onRepeatTimerTaskIs(ALTimerTaskStatus.ERROR, task)
                else:
                    task["status"] = ALTimerTaskStatus.ERROR
                break
        self.timerTasksChanged.emit()
