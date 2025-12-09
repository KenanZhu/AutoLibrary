# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtCore import (
    Qt, Signal
)
from PySide6.QtWidgets import (
    QFrame, QLabel
)


class ALSeatFrame(QFrame):

    clicked = Signal(str)

    def __init__(
        self,
        seat_number,
        parent=None
    ):

        super().__init__(parent)
        self.__seat_number = seat_number
        self.__is_selected = False
        self.setupUi()

    def setupUi(
        self
    ):

        self.setFixedSize(60, 40)
        self.setFrameStyle(QFrame.Box | QFrame.Plain)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                background-color: #4196EB;
                border: 2px solid #4196EB;
                border-radius: 5px;
            }
            QLabel {
                color: #F0F0F0;
                font-weight: bold;
            }
        """)
        self.label = QLabel(self.__seat_number, self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setGeometry(0, 0, 60, 40)

    def mousePressEvent(
        self,
        event
    ):

        if event.button() == Qt.LeftButton:
            self.toggleSelection()
            self.clicked.emit(self.__seat_number)


    def isSelected(
        self
    ):

        return self.__is_selected


    def toggleSelection(self):

        self.__is_selected = not self.__is_selected
        if self.__is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #4CAF50;
                    border: 2px solid #388E3C;
                    border-radius: 5px;
                    color: white;
                }
                QLabel {
                    color: #F0F0F0;
                    font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #4196EB;
                    border: 2px solid #4196EB;
                    border-radius: 5px;
                }
                QLabel {
                    color: #F0F0F0;
                    font-weight: bold;
                }
            """)