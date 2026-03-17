# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from datetime import datetime

from PySide6.QtCore import Slot, Qt
from PySide6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QHeaderView
)

from gui.ALTimerTaskAddDialog import ALTimerTaskStatus


class ALTimerTaskHistoryDialog(QDialog):

    def __init__(
        self,
        parent = None,
        task_data: dict = None
    ):

        super().__init__(parent)

        self.__task_data = task_data
        self.__history = task_data.get("history", [])

        self.modifyUi()
        self.connectSignals()


    def modifyUi(
        self
    ):

        self.setWindowTitle("定时任务执行历史 - AutoLibrary")
        self.setMinimumSize(300, 300)
        self.setMaximumSize(500, 400)

        MainLayout = QVBoxLayout(self)
        InfoLayout = QGridLayout()
        TaskNameLabel = QLabel(f"任务: {self.__task_data.get('name', '未命名')}")
        TaskNameLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        InfoLayout.addWidget(TaskNameLabel, 0, 0)
        TaskUUIDLabel = QLabel(f"UUID: {self.__task_data.get('task_uuid', '未命名')}")
        TaskUUIDLabel.setStyleSheet("font-size: 10px;")
        InfoLayout.addWidget(TaskUUIDLabel, 1, 0)
        InfoLayout.setColumnStretch(0, 1)

        if self.__task_data.get("repeat", False):
            RepeatLabel = QLabel("重复任务")
            RepeatLabel.setStyleSheet("color: #2294FF; font-weight: bold; font-size: 12px;")
            InfoLayout.addWidget(RepeatLabel, 0, 1)
        MainLayout.addLayout(InfoLayout)
        self.HistoryTableWidget = QTableWidget()
        self.HistoryTableWidget.setColumnCount(3)
        self.HistoryTableWidget.setHorizontalHeaderLabels(["执行时间", "结果", "耗时（秒/s）"])
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.HistoryTableWidget.verticalHeader().setVisible(False)
        self.HistoryTableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.HistoryTableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.loadHistory()
        MainLayout.addWidget(self.HistoryTableWidget)

        ButtonLayout = QHBoxLayout()
        ButtonLayout.addStretch()
        self.CloseButton = QPushButton("关闭")
        self.CloseButton.setFixedSize(80, 25)
        self.CloseButton.setDefault(True)
        self.ClearHistoryButton = QPushButton("清空历史")
        self.ClearHistoryButton.setFixedSize(80, 25)
        self.ClearHistoryButton.setStyleSheet("color: #DC0000;")
        ButtonLayout.addWidget(self.ClearHistoryButton)
        ButtonLayout.addWidget(self.CloseButton)
        MainLayout.addLayout(ButtonLayout)


    def connectSignals(
        self
    ):

        self.CloseButton.clicked.connect(self.accept)
        self.ClearHistoryButton.clicked.connect(self.onClearHistoryButtonClicked)


    def loadHistory(
        self
    ):

        self.HistoryTableWidget.setRowCount(len(self.__history))
        for row, record in enumerate(self.__history):
            self.addHistoryRow(row, record)


    def addHistoryRow(
        self,
        row: int,
        record: dict
    ):

        execute_time = record.get("execute_time", "")
        result = record.get("result", ALTimerTaskStatus.UNKNOWN)
        duration = record.get("duration", 0)
        ExecuteTimeItem = QTableWidgetItem(execute_time)
        ExecuteTimeItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.HistoryTableWidget.setItem(row, 0, ExecuteTimeItem)
        ResultItem = QTableWidgetItem(result.value)
        ResultItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        match result:
            case ALTimerTaskStatus.EXECUTED:
                ResultItem.setForeground(Qt.GlobalColor.green)
            case ALTimerTaskStatus.ERROR:
                ResultItem.setForeground(Qt.GlobalColor.red)
            case ALTimerTaskStatus.OUTDATED:
                ResultItem.setForeground(Qt.GlobalColor.red)
            case _:
                ResultItem.setForeground(Qt.GlobalColor.black)
        self.HistoryTableWidget.setItem(row, 1, ResultItem)
        DurationItem = QTableWidgetItem(f"{duration:.2f}")
        DurationItem.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.HistoryTableWidget.setItem(row, 2, DurationItem)
        self.HistoryTableWidget.setRowHeight(row, 25)

    @Slot()
    def onClearHistoryButtonClicked(
        self
    ):

        self.__history.clear()
        self.HistoryTableWidget.setRowCount(0)
        self.__task_data["history"] = self.__history


    def getHistory(
        self
    ) -> list:

        return self.__history
