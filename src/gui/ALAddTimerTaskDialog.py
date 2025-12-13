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
import uuid
import queue

from enum import Enum
from datetime import datetime, timedelta

from PySide6.QtCore import (
    Qt, Signal, Slot, QDateTime
)
from PySide6.QtWidgets import (
    QLabel, QDialog, QWidget, QSpinBox, QVBoxLayout,
    QHBoxLayout, QGridLayout, QDateTimeEdit
)
from PySide6.QtGui import (
    QCloseEvent
)

from gui.Ui_ALAddTimerTaskDialog import Ui_ALAddTimerTaskDialog


class TimerTaskStatus(Enum):

    PENDING = "等待中"
    READY = "已就绪"
    RUNNING = "执行中"
    EXECUTED = "已执行"
    ERROR = "执行失败"
    OUTDATED = "已过期"


class ALAddTimerTaskWidget(QDialog, Ui_ALAddTimerTaskDialog):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)

        self.setupUi(self)
        self.connectSignals()
        self.modifyUi()


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
        self.RelativeTimerLayout = QGridLayout(self.RelativeTimerWidget)
        self.RelativeTimerLayout.addWidget(QLabel("相对时间："), 0, 0)
        self.RelativeDaySpinBox = QSpinBox()
        self.RelativeDaySpinBox.setMinimum(0)
        self.RelativeDaySpinBox.setMaximum(365)
        self.RelativeDaySpinBox.setSuffix("天")
        self.RelativeTimerLayout.addWidget(self.RelativeDaySpinBox, 1, 0)
        self.RelativeHourSpinBox = QSpinBox()
        self.RelativeHourSpinBox.setMinimum(0)
        self.RelativeHourSpinBox.setMaximum(23)
        self.RelativeHourSpinBox.setSuffix("时")
        self.RelativeTimerLayout.addWidget(self.RelativeHourSpinBox, 1, 1)
        self.RelativeMinuteSpinBox = QSpinBox()
        self.RelativeMinuteSpinBox.setMinimum(0)
        self.RelativeMinuteSpinBox.setMaximum(59)
        self.RelativeMinuteSpinBox.setSuffix("分")
        self.RelativeTimerLayout.addWidget(self.RelativeMinuteSpinBox, 1, 2)
        self.RelativeSecondSpinBox = QSpinBox()
        self.RelativeSecondSpinBox.setMinimum(0)
        self.RelativeSecondSpinBox.setMaximum(59)
        self.RelativeSecondSpinBox.setSuffix("秒")
        self.RelativeTimerLayout.addWidget(self.RelativeSecondSpinBox, 1, 3)
        self.TimerConfigLayout.addWidget(self.RelativeTimerWidget)
        self.RelativeTimerWidget.setVisible(False)


    def connectSignals(
        self
    ):

        self.CancelButton.clicked.connect(self.reject)
        self.ConfirmButton.clicked.connect(self.accept)
        self.TimerTypeComboBox.currentIndexChanged.connect(self.onTimerTypeComboBoxIndexChanged)


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
        return {
            "name": name,
            "task_uuid": uuid.uuid4().hex.upper() + f"-{added_time.strftime("%Y%m%d%H%M%S")}",
            "time_type": self.TimerTypeComboBox.currentText(),
            "execute_time": execute_time,
            "silent": silent,
            "add_time": added_time,
            "status": TimerTaskStatus.PENDING,
            "executed": False
        }


    @Slot(int)
    def onTimerTypeComboBoxIndexChanged(
        self,
        index: int
    ):

        self.SpecificTimerWidget.setVisible(index == 0)
        self.RelativeTimerWidget.setVisible(index == 1)