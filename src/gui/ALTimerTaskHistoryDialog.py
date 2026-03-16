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
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QHeaderView
)


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

    def modifyUi(
        self
    ):

        self.setWindowTitle("定时任务执行历史 - AutoLibrary")
        self.setMinimumSize(600, 400)

        MainLayout = QVBoxLayout(self)

        InfoLayout = QHBoxLayout()
        TaskNameLabel = QLabel(f"任务: {self.__task_data.get('name', '未命名')}")
        TaskNameLabel.setStyleSheet("font-weight: bold; font-size: 14px;")
        InfoLayout.addWidget(TaskNameLabel)
        InfoLayout.addStretch()

        if self.__task_data.get("repeat", False):
            repeat_label = QLabel("重复任务")
            repeat_label.setStyleSheet("color: #2294FF; font-weight: bold;")
            InfoLayout.addWidget(repeat_label)
        MainLayout.addLayout(InfoLayout)
        self.HistoryTableWidget = QTableWidget()
        self.HistoryTableWidget.setColumnCount(4)
        self.HistoryTableWidget.setHorizontalHeaderLabels(["执行时间", "结果", "耗时（秒/s）", "uuid"])
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.HistoryTableWidget.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.HistoryTableWidget.verticalHeader().setVisible(False)
        self.HistoryTableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.HistoryTableWidget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._loadHistory()
        MainLayout.addWidget(self.HistoryTableWidget)

        ButtonLayout = QHBoxLayout()
        ButtonLayout.addStretch()
        self.CloseButton = QPushButton("关闭")
        self.CloseButton.setFixedSize(80, 25)
        self.CloseButton.clicked.connect(self.accept)
        self.ClearHistoryButton = QPushButton("清空历史")
        self.ClearHistoryButton.setFixedSize(80, 25)
        self.ClearHistoryButton.clicked.connect(self._clearHistory)
        ButtonLayout.addWidget(self.ClearHistoryButton)
        ButtonLayout.addWidget(self.CloseButton)
        MainLayout.addLayout(ButtonLayout)


    def _loadHistory(
        self
    ):

        self.HistoryTableWidget.setRowCount(len(self.__history))
        for row, record in enumerate(self.__history):
            self._addHistoryRow(row, record)


    def _addHistoryRow(
        self,
        row: int,
        record: dict
    ):

        execute_time_str = record.get("execute_time", "")
        result = record.get("result", "未知")
        duration = record.get("duration", 0)
        uuid = record.get("uuid", "")
        self.HistoryTableWidget.setItem(row, 0, QTableWidgetItem(execute_time_str))
        self.HistoryTableWidget.setItem(row, 1, QTableWidgetItem(result))
        duration_item = QTableWidgetItem(f"{duration:.2f}")
        duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.HistoryTableWidget.setItem(row, 2, duration_item)
        self.HistoryTableWidget.setItem(row, 3, QTableWidgetItem(uuid))
        if result == "成功":
            self.HistoryTableWidget.item(row, 1).setForeground(Qt.GlobalColor.green)
        elif result == "失败":
            self.HistoryTableWidget.item(row, 1).setForeground(Qt.GlobalColor.red)

    @Slot()
    def _clearHistory(
        self
    ):

        self.__history.clear()
        self.HistoryTableWidget.setRowCount(0)
        self.__task_data["history"] = self.__history


    def getHistory(
        self
    ) -> list:

        return self.__history
