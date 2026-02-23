# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtCore import (
    Qt, Slot, QEvent
)
from PySide6.QtWidgets import (
    QFrame, QWidget,
    QGridLayout, QGraphicsView, QGraphicsScene, QGraphicsItem
)
from PySide6.QtGui import (
    QPainter, QWheelEvent
)

from gui.ALSeatFrame import ALSeatFrame


class ALSeatMapView(QGraphicsView):

    def __init__(
        self,
        parent: QWidget = None,
        seats_data: dict = {},
    ):
        super().__init__(parent)
        self.__seats_data = seats_data
        self.__selected_seats = []
        self.__seat_frames = {}

        self.setupUi()

    @staticmethod
    def formatSeatNumber(
        seat_number: str
    ) -> str:

        if seat_number and not seat_number[-1].isdigit():
            digits = seat_number[:-1]
            letter = seat_number[-1]
            return digits.zfill(3) + letter
        return seat_number.zfill(3)


    def eventFilter(
        self,
        watched,
        event
    ):

        if (watched is self.viewport() and
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
        min_scale = 0.1
        max_scale = 4.0
        current_scale = self.transform().m11()
        zoom_factor = 1.2 if delta > 0 else 1/1.2
        target_scale = current_scale*zoom_factor
        if target_scale < min_scale and delta < 0:
            return
        if target_scale > max_scale and delta > 0:
            return
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.scale(zoom_factor, zoom_factor)


    def setupUi(
        self
    ):

        self.SeatMapGraphicsScene = QGraphicsScene(self)
        self.setScene(self.SeatMapGraphicsScene)
        self.setRenderHint(QPainter.RenderHint.LosslessImageRendering)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.viewport().installEventFilter(self)

        self.SeatsContainerWidget = QWidget()
        self.SeatsContainerLayout = QGridLayout(self.SeatsContainerWidget)
        self.setupSeatMap()

        self.ContainerProxy = self.SeatMapGraphicsScene.addWidget(self.SeatsContainerWidget)
        self.ContainerProxy.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, False)


    def setupSeatMap(
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