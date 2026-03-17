# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import uuid

from enum import Enum
from datetime import datetime, timedelta

from PySide6.QtCore import Slot, QDateTime
from PySide6.QtWidgets import QLabel, QDialog, QWidget, QSpinBox, QHBoxLayout, QGridLayout, QDateTimeEdit

from gui.resources.ui.Ui_ALTimerTaskAddDialog import Ui_ALTimerTaskAddDialog
import utils.TimerUtils as TimerUtils


class ALTimerTaskStatus(Enum):

    PENDING = "等待中"
    READY = "已就绪"
    RUNNING = "执行中"
    EXECUTED = "已执行"
    ERROR = "执行失败"
    OUTDATED = "已过期"
    UNKNOWN = "未知"


class ALTimerTaskAddDialog(QDialog, Ui_ALTimerTaskAddDialog):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()


    def modifyUi(
        self
    ):

        self.TimerTypeComboBox.setCurrentIndex(0)
        self.SpecificTimerWidget = QWidget()
        self.SpecificTimerLayout = QHBoxLayout(self.SpecificTimerWidget)
        self.SpecificTimerLayout.addWidget(QLabel("定时时间："))
        self.SpecificDateTimeEdit = QDateTimeEdit()
        self.SpecificDateTimeEdit.setCalendarPopup(True)
        self.SpecificDateTimeEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.SpecificDateTimeEdit.setMinimumDateTime(QDateTime.currentDateTime())
        self.SpecificDateTimeEdit.setDateTime(QDateTime.currentDateTime().addSecs(60))
        self.SpecificTimerLayout.addWidget(self.SpecificDateTimeEdit)
        self.TimerConfigLayout.addWidget(self.SpecificTimerWidget)

        self.RelativeTimerWidget = QWidget()
        self.RelativeTimerLayout = QHBoxLayout(self.RelativeTimerWidget)
        self.RelativeTimerLayout.addWidget(QLabel("相对时间："))
        self.RelativeDaySpinBox = QSpinBox()
        self.RelativeDaySpinBox.setMinimum(0)
        self.RelativeDaySpinBox.setMaximum(364)
        self.RelativeDaySpinBox.setSuffix("天")
        self.RelativeTimerLayout.addWidget(self.RelativeDaySpinBox)
        self.RelativeHourSpinBox = QSpinBox()
        self.RelativeHourSpinBox.setMinimum(0)
        self.RelativeHourSpinBox.setMaximum(23)
        self.RelativeHourSpinBox.setSuffix("时")
        self.RelativeTimerLayout.addWidget(self.RelativeHourSpinBox)
        self.RelativeMinuteSpinBox = QSpinBox()
        self.RelativeMinuteSpinBox.setMinimum(0)
        self.RelativeMinuteSpinBox.setMaximum(59)
        self.RelativeMinuteSpinBox.setSuffix("分")
        self.RelativeTimerLayout.addWidget(self.RelativeMinuteSpinBox)
        self.RelativeSecondSpinBox = QSpinBox()
        self.RelativeSecondSpinBox.setMinimum(0)
        self.RelativeSecondSpinBox.setMaximum(59)
        self.RelativeSecondSpinBox.setSuffix("秒")
        self.RelativeTimerLayout.addWidget(self.RelativeSecondSpinBox)
        self.TimerConfigLayout.addWidget(self.RelativeTimerWidget)
        self.RelativeTimerWidget.setVisible(False)


    def connectSignals(
        self
    ):

        self.CancelButton.clicked.connect(self.reject)
        self.ConfirmButton.clicked.connect(self.accept)
        self.TimerTypeComboBox.currentIndexChanged.connect(self.onTimerTypeComboBoxIndexChanged)
        self.RepeatCheckBox.toggled.connect(self.onRepeatCheckBoxToggled)


    def getTimerTask(
        self
    ) -> dict:

        added_time = datetime.now()
        if not self.TaskNameLineEdit.text():
            name = f"未命名任务-{added_time.strftime("%Y%m%d%H%M%S")}"
        else:
            name = self.TaskNameLineEdit.text()
        timer_type_index = self.TimerTypeComboBox.currentIndex()
        silent = not self.ShowBeforeRunRadioButton.isChecked()
        if timer_type_index == 0:
            execute_time = self.SpecificDateTimeEdit.dateTime()
            tmp_time_str = execute_time.toString("yyyy-MM-dd HH:mm:ss")
            execute_time = datetime.strptime(tmp_time_str, "%Y-%m-%d %H:%M:%S")
        else:
            execute_time = datetime.now() + timedelta(
                days = self.RelativeDaySpinBox.value(),
                hours = self.RelativeHourSpinBox.value(),
                minutes = self.RelativeMinuteSpinBox.value(),
                seconds = self.RelativeSecondSpinBox.value()
            )
        task_data = {
            "name": name,
            "task_uuid": uuid.uuid4().hex.upper() + f"-{added_time.strftime("%Y%m%d%H%M%S")}",
            "time_type": self.TimerTypeComboBox.currentText(),
            "execute_time": execute_time,
            "silent": silent,
            "add_time": added_time,
            "status": ALTimerTaskStatus.PENDING,
            "executed": False,
            "repeat": self.RepeatCheckBox.isChecked(),
        }
        if task_data["repeat"]:
            repeat_days = []
            if self.MonCheckBox.isChecked():
                repeat_days.append(0)
            if self.TueCheckBox.isChecked():
                repeat_days.append(1)
            if self.WedCheckBox.isChecked():
                repeat_days.append(2)
            if self.ThuCheckBox.isChecked():
                repeat_days.append(3)
            if self.FriCheckBox.isChecked():
                repeat_days.append(4)
            if self.SatCheckBox.isChecked():
                repeat_days.append(5)
            if self.SunCheckBox.isChecked():
                repeat_days.append(6)
            if not repeat_days:
                repeat_days = [0, 1, 2, 3, 4, 5, 6]
            task_data["repeat_days"] = repeat_days
            task_data["repeat_hour"] = execute_time.hour
            task_data["repeat_minute"] = execute_time.minute
            task_data["repeat_second"] = execute_time.second
            task_data["execute_time"] = TimerUtils.calculateNextRepeatTime(
                task_data["repeat_days"],
                task_data["repeat_hour"],
                task_data["repeat_minute"],
                task_data["repeat_second"]
            )

        return task_data

    @Slot(int)
    def onTimerTypeComboBoxIndexChanged(
        self,
        index: int
    ):

        self.SpecificTimerWidget.setVisible(index == 0)
        self.RelativeTimerWidget.setVisible(index == 1)

    @Slot(bool)
    def onRepeatCheckBoxToggled(
        self,
        checked: bool
    ):

        self.MonCheckBox.setEnabled(checked)
        self.TueCheckBox.setEnabled(checked)
        self.WedCheckBox.setEnabled(checked)
        self.ThuCheckBox.setEnabled(checked)
        self.FriCheckBox.setEnabled(checked)
        self.SatCheckBox.setEnabled(checked)
        self.SunCheckBox.setEnabled(checked)