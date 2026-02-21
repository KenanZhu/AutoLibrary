# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtCore import (
    Qt, Slot, Signal
)
from PySide6.QtWidgets import (
    QDialog, QLabel, QHBoxLayout, QVBoxLayout,
    QPushButton,
)
from PySide6.QtGui import (
    QCloseEvent
)
from gui.ALSeatMapView import ALSeatMapView


class ALSeatMapSelectDialog(QDialog):

    seatMapSelectDialogIsClosed = Signal(list)

    def __init__(
        self,
        parent: QDialog = None,
        floor: str = "",
        room: str = "",
        seats_data: str = ""
    ):

        super().__init__(parent)
        self.__floor = floor
        self.__room = room
        self.__seats_data = seats_data
        self.__confirmed = False

        self.setupUi()
        self.connectSignals()


    def setupUi(
        self
    ):

        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        self.setWindowTitle(f"选择楼层座位 - AutoLibrary")

        self.SeatMapWidgetMainLayout = QVBoxLayout(self)
        self.SeatMapWidgetMainLayout.setContentsMargins(5, 5, 5, 5)
        self.SeatMapWidgetMainLayout.setSpacing(5)
        self.TitleLabel = QLabel(f"楼层座位分布图: {self.__floor}-{self.__room}")
        self.TitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.TitleLabel.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        self.SeatMapWidgetMainLayout.addWidget(self.TitleLabel)

        self.SeatMapGraphicsView = ALSeatMapView(None, self.__seats_data)
        self.SeatMapWidgetMainLayout.addWidget(self.SeatMapGraphicsView)

        self.TipsLabel = QLabel(
            "  点击座位进行选择/取消选择, 最多选择1个座位 \n"
            "  [操作方法: Ctrl+鼠标滚轮缩放 | 滚轮/拖拽/方向键 移动]"
        )
        self.TipsLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.TipsLabel.setStyleSheet("color: #666; margin: 5px;")
        self.SeatMapWidgetMainLayout.addWidget(self.TipsLabel)

        self.ConfirmButton = QPushButton("确认")
        self.ConfirmButton.setFixedSize(80, 25)
        self.ConfirmButton.setAutoDefault(True)
        self.ConfirmButton.setDefault(True)
        self.CancelButton = QPushButton("取消")
        self.CancelButton.setFixedSize(80, 25)
        self.SeatMapWidgetControlLayout = QHBoxLayout()
        self.SeatMapWidgetControlLayout.setContentsMargins(0, 0, 0, 0)
        self.SeatMapWidgetControlLayout.setSpacing(5)
        self.SeatMapWidgetControlLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.SeatMapWidgetControlLayout.addWidget(self.CancelButton)
        self.SeatMapWidgetControlLayout.addWidget(self.ConfirmButton)
        self.SeatMapWidgetMainLayout.addLayout(self.SeatMapWidgetControlLayout)


    def connectSignals(
        self
    ):

        self.ConfirmButton.clicked.connect(self.onConfirmButtonClicked)
        self.CancelButton.clicked.connect(self.onCancelButtonClicked)


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

        if not self.__confirmed:
            self.clearSelections()
            self.reject()
        else:
            self.accept()
        self.seatMapSelectDialogIsClosed.emit(self.getSelectedSeats())
        super().closeEvent(event)


    def selectSeat(
        self,
        seat_number: str
    ):

        self.SeatMapGraphicsView.selectSeat(seat_number)


    def selectSeats(
        self,
        seat_numbers: list[str]
    ) -> bool:

        return self.SeatMapGraphicsView.selectSeats(seat_numbers)


    def getSelectedSeats(
        self
    ) -> list[str]:

        return self.SeatMapGraphicsView.getSelectedSeats()


    def clearSelections(
        self
    ):

        self.SeatMapGraphicsView.clearSelections()

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        self.__confirmed = True
        self.accept()

    @Slot()
    def onCancelButtonClicked(
        self
    ):

        self.__confirmed = False
        self.reject()
