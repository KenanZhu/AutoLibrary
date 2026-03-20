
from enum import Enum

from PySide6.QtWidgets import (
    QLabel
)
from PySide6.QtCore import (
    Qt, Property, QPropertyAnimation, QEasingCurve
)
from PySide6.QtGui import (
    QPainter, QColor, QConicalGradient, QPalette
)


class ALStatusLabel(QLabel):

    class Status(Enum):
        """
            Enum class for representing the status of ALStatusLabel.
        """

        WAITING = 0
        RUNNING = 1
        SUCCESS = 2
        WARNING = 3
        FAILURE = 4

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self.__status = self.Status.WAITING
        self.__icon_angle = 0

        self.setupUi()


    def setupUi(
        self
    ):

        self.setFixedSize(36, 36)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.RunningAnimation = QPropertyAnimation(self, b"iconAngle")
        self.RunningAnimation.setDuration(1000)
        self.RunningAnimation.setStartValue(0)
        self.RunningAnimation.setEndValue(-360)
        self.RunningAnimation.setLoopCount(-1)
        self.RunningAnimation.setEasingCurve(QEasingCurve.Type.Linear)


    def isDarkMode(
        self
    ) -> bool:

        return self.palette().color(QPalette.ColorRole.Window).value() < 128


    def getMarkColor(
        self
    ) -> QColor:

        return QColor("#FFFFFF") if self.isDarkMode() else QColor("#454545")

    @Property(Status)
    def status(
        self
    ) -> Status:

        return self.__status

    @Property(int)
    def iconAngle(
        self
    ) -> int:

        return self.__icon_angle

    @status.setter
    def status(
        self,
        status: Status
    ):

        if status not in self.Status:
            raise ValueError(f"Invalid (class)Status[enum.Enum] value: {status}")
        self.__status = status
        if self.__status == self.Status.RUNNING:
            self.RunningAnimation.start()
        else:
            self.RunningAnimation.stop()
        self.update()

    @iconAngle.setter
    def iconAngle(
        self,
        value: int
    ):

        self.__icon_angle = value
        self.update()


    def paintEvent(
        self,
        event
    ):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        center_x = self.width()/2
        center_y = self.height()/2
        radius = min(center_x, center_y) - 3
        match self.__status:
            case self.Status.WAITING:
                pen = painter.pen()
                pen.setWidth(2)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setColor(QColor("#969696")) # grey
                painter.setPen(pen)
                painter.drawEllipse(
                    int(center_x - radius),
                    int(center_y - radius),
                    int(radius*2),
                    int(radius*2)
                )
            case self.Status.RUNNING:
                gradient = QConicalGradient(center_x, center_y, self.__icon_angle)
                gradient.setColorAt(0.0, QColor("#2294FF" if self.isDarkMode() else "#0094FF"))
                gradient.setColorAt(1.0, QColor("#2294FF00"))
                pen = painter.pen()
                pen.setWidth(3)
                pen.setBrush(gradient)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawEllipse(
                    int(center_x - radius),
                    int(center_y - radius),
                    int(radius*2),
                    int(radius*2)
                )
            case self.Status.SUCCESS:
                # draw the success green circle
                pen = painter.pen()
                pen.setWidth(2)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setColor(QColor("#4CAF50" if self.isDarkMode() else "#00AF50")) # green
                painter.setPen(pen)
                painter.drawEllipse(
                    int(center_x - radius),
                    int(center_y - radius),
                    int(radius*2),
                    int(radius*2)
                )
                # draw the success check mark '✓'
                painter.setPen(Qt.PenStyle.SolidLine)
                pen = painter.pen()
                pen.setWidth(3)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                # white when dark mode, black when light mode
                pen.setColor(self.getMarkColor())
                painter.setPen(pen)
                mark_size = radius/2
                mark_path = [
                    (center_x - mark_size, center_y),
                    (center_x - mark_size/3, center_y + mark_size/2),
                    (center_x + mark_size, center_y - mark_size/2)
                ]
                painter.drawLine(
                    int(mark_path[0][0]),int(mark_path[0][1]),
                    int(mark_path[1][0]),int(mark_path[1][1])
                )
                painter.drawLine(
                    int(mark_path[1][0]),int(mark_path[1][1]),
                    int(mark_path[2][0]),int(mark_path[2][1])
                )
            case self.Status.WARNING:
                # draw the warning orange circle
                pen = painter.pen()
                pen.setWidth(2)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setColor(QColor("#FF9800")) # orange
                painter.setPen(pen)
                painter.drawEllipse(
                    int(center_x - radius),
                    int(center_y - radius),
                    int(radius*2),
                    int(radius*2)
                )
                # draw the warning exclamation mark '!'
                painter.setPen(Qt.PenStyle.SolidLine)
                pen = painter.pen()
                pen.setWidth(3)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                # white when dark mode, black when light mode
                pen.setColor(self.getMarkColor())
                painter.setPen(pen)
                painter.drawLine(
                    int(center_x), int(center_y - radius/2),
                    int(center_x), int(center_y + radius/6)
                )
                painter.drawPoint(
                    int(center_x), int(center_y + radius/2)
                )
            case self.Status.FAILURE:
                # draw the failure red circle
                pen = painter.pen()
                pen.setWidth(2)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                pen.setColor(QColor("#DC0000")) # red
                painter.setPen(pen)
                painter.drawEllipse(
                    int(center_x - radius),
                    int(center_y - radius),
                    int(radius*2),
                    int(radius*2)
                )
                # draw the failure cross mark '✗'
                painter.setPen(Qt.PenStyle.SolidLine)
                pen = painter.pen()
                pen.setWidth(3)
                pen.setBrush(Qt.BrushStyle.NoBrush)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                # white when dark mode, black when light mode
                pen.setColor(self.getMarkColor())
                painter.setPen(pen)
                mark_size = radius/3
                painter.drawLine(
                    int(center_x - mark_size), int(center_y - mark_size),
                    int(center_x + mark_size), int(center_y + mark_size)
                )
                painter.drawLine(
                    int(center_x + mark_size), int(center_y - mark_size),
                    int(center_x - mark_size), int(center_y + mark_size)
                )
        painter.end()
        super().paintEvent(event)
