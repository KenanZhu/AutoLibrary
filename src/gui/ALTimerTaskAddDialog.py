# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import uuid

from enum import Enum
from datetime import datetime, timedelta

from PySide6.QtCore import Slot, QDateTime, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLabel, QDialog, QWidget, QSpinBox, QHBoxLayout, QVBoxLayout, QGridLayout, QDateTimeEdit, QGroupBox, QPushButton

from gui.resources.ui.Ui_ALTimerTaskAddDialog import Ui_ALTimerTaskAddDialog
from gui.ALAutoScriptOrchDialog import ALAutoScriptOrchDialog
from utils.TimerUtils import TimerUtils


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
        parent = None,
        timer_task: dict = None
    ):

        super().__init__(parent)
        self.__edit_timer_task = timer_task

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()

        if self.__edit_timer_task:
            self.loadTask(self.__edit_timer_task)


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

        self.AutoScriptGroupBox = QGroupBox("AutoScript 指令")
        self.AutoScriptLayout = QVBoxLayout(self.AutoScriptGroupBox)
        self.AutoScriptLayout.setContentsMargins(3, 3, 3, 3)
        self.AutoScriptLayout.setSpacing(3)
        autoScriptBtnLayout = QHBoxLayout()
        self.AutoScriptSetButton = QPushButton("设置指令")
        self.AutoScriptSetButton.setMinimumHeight(25)
        self.AutoScriptSetButton.setFixedWidth(130)
        autoScriptBtnLayout.addWidget(self.AutoScriptSetButton)
        self.AutoScriptPreviewButton = QPushButton("预览")
        self.AutoScriptPreviewButton.setMinimumHeight(25)
        self.AutoScriptPreviewButton.setFixedWidth(60)
        self.AutoScriptPreviewButton.setEnabled(False)
        autoScriptBtnLayout.addWidget(self.AutoScriptPreviewButton)
        autoScriptBtnLayout.addStretch()
        self.AutoScriptHelpButton = QPushButton("?")
        self.AutoScriptHelpButton.setFixedSize(20, 20)
        self.AutoScriptHelpButton.setToolTip(
            "AutoScript 是一种轻量级 DSL\n"
            "用于在重复定时任务执行前，对用户的预约数据进行预处理\n"
            "\n"
            "点击查看完整在线文档"
        )
        self.AutoScriptHelpButton.setStyleSheet(
            "QPushButton { border-radius: 10px; border: 1px solid #999; "
            "font-weight: bold; color: #555; }"
            "QPushButton:hover { background-color: #E0E0E0; }"
        )
        autoScriptBtnLayout.addWidget(self.AutoScriptHelpButton)
        self.AutoScriptStatusLabel = QLabel("未设置")
        self.AutoScriptStatusLabel.setStyleSheet("color: #969696;")
        self.AutoScriptStatusLabel.setFixedHeight(25)
        autoScriptBtnLayout.addWidget(self.AutoScriptStatusLabel)
        self.AutoScriptLayout.addLayout(autoScriptBtnLayout)
        self.ALAddTimerTaskLayout.insertWidget(
            self.ALAddTimerTaskLayout.indexOf(self.TaskConfigGroupBox) + 1,
            self.AutoScriptGroupBox
        )
        self.AutoScriptGroupBox.setVisible(False)
        self.__auto_script = ""


    def loadTask(
        self,
        task: dict
    ):

        self.TaskNameLineEdit.setText(task.get("name", ""))
        time_type = task.get("time_type", "特定时间")
        self.TimerTypeComboBox.setCurrentText(time_type)
        self.SpecificDateTimeEdit.setDateTime(
            QDateTime(task["execute_time"])
        )
        self.RelativeDaySpinBox.setValue(0)
        self.RelativeHourSpinBox.setValue(0)
        self.RelativeMinuteSpinBox.setValue(0)
        self.RelativeSecondSpinBox.setValue(0)
        if task.get("silent", False):
            self.SilentlyRunRadioButton.setChecked(True)
        else:
            self.ShowBeforeRunRadioButton.setChecked(True)
        repeat = task.get("repeat", False)
        self.RepeatCheckBox.setChecked(repeat)
        if repeat:
            repeat_days = task.get("repeat_days", [])
            self.MonCheckBox.setChecked(0 in repeat_days)
            self.TueCheckBox.setChecked(1 in repeat_days)
            self.WedCheckBox.setChecked(2 in repeat_days)
            self.ThuCheckBox.setChecked(3 in repeat_days)
            self.FriCheckBox.setChecked(4 in repeat_days)
            self.SatCheckBox.setChecked(5 in repeat_days)
            self.SunCheckBox.setChecked(6 in repeat_days)
            auto_script = task.get("repeat_auto_script", "")
            if auto_script:
                self.__auto_script = auto_script
                self.AutoScriptStatusLabel.setText("已设置")
                self.AutoScriptStatusLabel.setStyleSheet("color: #4CAF50;")
                self.AutoScriptPreviewButton.setEnabled(True)
        self.ConfirmButton.setText("保存")


    def connectSignals(
        self
    ):

        self.CancelButton.clicked.connect(self.reject)
        self.ConfirmButton.clicked.connect(self.accept)
        self.TimerTypeComboBox.currentIndexChanged.connect(self.onTimerTypeComboBoxIndexChanged)
        self.RepeatCheckBox.toggled.connect(self.onRepeatCheckBoxToggled)
        self.AutoScriptSetButton.clicked.connect(self.onSetAutoScript)
        self.AutoScriptPreviewButton.clicked.connect(self.onPreviewAutoScript)
        self.AutoScriptHelpButton.clicked.connect(self.onAutoScriptHelp)


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

        if self.__edit_timer_task:
            task_data = dict(self.__edit_timer_task)
            task_data["name"] = name
            task_data["execute_time"] = execute_time
            task_data["silent"] = silent
            task_data["status"] = ALTimerTaskStatus.PENDING
            task_data["executed"] = False
            task_data["repeat_auto_script"] = self.__auto_script
        else:
            task_data = {
                "name": name,
                "uuid": uuid.uuid4().hex.upper() + f"-{added_time.strftime("%Y%m%d%H%M%S")}",
                "time_type": self.TimerTypeComboBox.currentText(),
                "execute_time": execute_time,
                "silent": silent,
                "added_time": added_time,
                "status": ALTimerTaskStatus.PENDING,
                "executed": False,
                "repeat": self.RepeatCheckBox.isChecked(),
                "repeat_auto_script": self.__auto_script,
            }

        repeat = self.RepeatCheckBox.isChecked()
        task_data["repeat"] = repeat
        if repeat:
            if "repeat_history" not in task_data:
                task_data["repeat_history"] = []
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
            task_data["execute_time"] = TimerUtils.getNextTimerRepeatTime(
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
        self.AutoScriptGroupBox.setVisible(checked)

    @Slot()
    def onSetAutoScript(self):
        dlg = ALAutoScriptOrchDialog(self, existingScript=self.__auto_script)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            script = dlg.getScript()
            self.__auto_script = script
            if script:
                self.AutoScriptStatusLabel.setText("已设置")
                self.AutoScriptStatusLabel.setStyleSheet("color: #4CAF50;")
                self.AutoScriptPreviewButton.setEnabled(True)
            else:
                self.AutoScriptStatusLabel.setText("未设置")
                self.AutoScriptStatusLabel.setStyleSheet("color: #969696;")
                self.AutoScriptPreviewButton.setEnabled(False)
        dlg.deleteLater()

    @Slot()
    def onPreviewAutoScript(self):
        if not self.__auto_script:
            return
        from gui.ALAutoScriptPrevDialog import ALAutoScriptPreviewDialog
        dlg = ALAutoScriptPreviewDialog(self, self.__auto_script)
        dlg.exec()
        dlg.deleteLater()

    @Slot()
    def onAutoScriptHelp(
        self
    ):

        QDesktopServices.openUrl(
            QUrl("https://www.autolibrary.kenanzhu.com/manuals/autoscript")
        )


