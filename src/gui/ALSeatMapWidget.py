# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtCore import (
    Qt, Slot, Signal, QEvent
)
from PySide6.QtWidgets import (
    QFrame, QWidget, QLabel, QHBoxLayout, QVBoxLayout,
    QGridLayout, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QPushButton,
)
from PySide6.QtGui import (
    QPainter, QWheelEvent, QCloseEvent
)
from gui.ALSeatFrame import ALSeatFrame


class ALSeatMapWidget(QWidget):

    seatMapWidgetClosed = Signal(list)

    def __init__(
        self,
        parent: QWidget = None,
        floor: str = "",
        room: str = "",
        seats_data: dict = {},
    ):

        super().__init__(parent)

        self.__floor = floor
        self.__room = room
        self.__seats_data = seats_data
        self.__selected_seats = []
        self.__seat_frames = {}
        self.setupUi()
        self.connectSignals()

    @staticmethod
    def formatSeatNumber(
        seat_number: str
    ) -> str:

        if seat_number and not seat_number[-1].isdigit():
            digits = seat_number[:-1]
            letter = seat_number[-1]
            return digits.zfill(3) + letter
        return seat_number.zfill(3)


    def setupUi(
        self
    ):

        self.setWindowFlags(Qt.WindowType.Window)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(800, 600)
        self.resize(800, 600)
        self.setWindowTitle(f"选择楼层座位 - AutoLibrary")

        self.SeatMapWidgetMainLayout = QVBoxLayout(self)
        self.TitleLabel = QLabel(f"楼层座位分布图: {self.__floor}-{self.__room}")
        self.TitleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.TitleLabel.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        self.SeatMapWidgetMainLayout.addWidget(self.TitleLabel)

        self.SeatMapGraphicsView = QGraphicsView(self)
        self.SeatMapGraphicsScene = QGraphicsScene(self)
        self.SeatMapGraphicsView.setScene(self.SeatMapGraphicsScene)
        self.SeatMapGraphicsView.setRenderHint(QPainter.RenderHint.LosslessImageRendering)
        self.SeatMapGraphicsView.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.SeatMapGraphicsView.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.SeatMapGraphicsView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.SeatMapGraphicsView.viewport().installEventFilter(self)

        self.SeatsContainerWidget = QWidget()
        self.SeatsContainerLayout = QGridLayout(self.SeatsContainerWidget)
        self.createSeatMap()

        self.ContainerProxy = self.SeatMapGraphicsScene.addWidget(self.SeatsContainerWidget)
        self.ContainerProxy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)
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
        self.CancelButton = QPushButton("取消")
        self.CancelButton.setFixedSize(80, 25)
        self.SeatMapWidgetControlLayout = QHBoxLayout()
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

        self.seatMapWidgetClosed.emit(self.__selected_seats)
        super().closeEvent(event)


    def eventFilter(
        self,
        watched,
        event
    ):

        if (watched is self.SeatMapGraphicsView.viewport() and
            event.type() == QEvent.Type.Wheel and
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.zoomGraphicsView(event)
            return True
        return super().eventFilter(watched, event)


    def zoomGraphicsView(
        self,
        event: QWheelEvent
    ):

        delta = event.angleDelta().y()
        zoom_factor = 1.2 if delta > 0 else 1/1.2
        self.SeatMapGraphicsView.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.SeatMapGraphicsView.scale(zoom_factor, zoom_factor)


    def createSeatMap(
        self
    ):

        rows = self.__seats_data.strip().split("\n")
        for row_idx, row in enumerate(rows):
            col_idx = 0
            seats_number = [seat.strip() for seat in row.split(",")]
            for seat_number in seats_number:
                if seat_number:
                    seat_widget = ALSeatFrame(seat_number)
                    seat_widget.clicked.connect(self.onSeatClicked)
                    self.SeatsContainerLayout.addWidget(seat_widget, row_idx, col_idx)
                    self.__seat_frames[seat_number] = seat_widget
                else:
                    spacer = QFrame()
                    spacer.setFixedSize(20, 30)
                    spacer.setStyleSheet("background-color: transparent; border: none;")
                    self.SeatsContainerLayout.addWidget(spacer, row_idx, col_idx)
                col_idx += 1
        self.SeatsContainerLayout.setSpacing(20)
        self.SeatsContainerLayout.setContentsMargins(20, 20, 20, 20)
        self.SeatsContainerWidget.adjustSize()


    def selectSeat(
        self,
        seat_number: str
    ):

        if len(self.__selected_seats) >= 1:
            return
        seat_number = self.formatSeatNumber(seat_number)
        if seat_number not in self.__seat_frames:
            return
        widget = self.__seat_frames[seat_number]
        if widget.isSelected():
            return
        widget.toggleSelection()
        self.__selected_seats.append(seat_number)


    def selectSeats(
        self,
        selected_seats: list
    ):

        self.clearSelections()
        for seat_number in selected_seats:
            self.selectSeat(seat_number)


    def getSelectedSeats(
        self
    ) -> list[str]:

        return self.__selected_seats


    def clearSelections(
        self
    ):

        seats_to_clear = self.__selected_seats.copy()
        for seat_number in seats_to_clear:
            if seat_number not in self.__seat_frames:
                continue
            widget = self.__seat_frames[seat_number]
            if widget.isSelected():
                widget.toggleSelection()
        self.__selected_seats = []

    @Slot(str)
    def onSeatClicked(
        self,
        seat_number: str
    ):

        if seat_number in self.__selected_seats:
            self.__selected_seats.remove(seat_number)
        else:
            if len(self.__selected_seats) < 1:
                self.__selected_seats.append(seat_number)
            else:
                self.__seat_frames[seat_number].toggleSelection()

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        self.close()

    @Slot()
    def onCancelButtonClicked(
        self
    ):

        self.clearSelections()
        self.close()