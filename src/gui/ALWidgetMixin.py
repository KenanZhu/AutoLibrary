# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtGui import QShowEvent


class CenterOnParentMixin:
    """
        Mixin that centres the widget relative to its parent on first show,
        clamping the position to the screen bounds.

        Usage::

            class MyWidget(CenterOnParentMixin, QWidget, Ui_MyWidget):
                pass

            class MyDialog(CenterOnParentMixin, QDialog):
                pass

        The mixin must appear **before** QWidget / QDialog in the base list
        so that ``super().showEvent(event)`` resolves up the MRO correctly.
    """

    def showEvent(
        self,
        event: QShowEvent
    ):

        super().showEvent(event)
        if self.parent():
            screen_rect = self.screen().geometry()
            target_pos = self.parent().geometry().center()
            target_pos.setX(target_pos.x() - self.width() // 2)
            target_pos.setY(target_pos.y() - self.height() // 2)
            if target_pos.x() < 0:
                target_pos.setX(0)
            if target_pos.x() + self.width() > screen_rect.width():
                target_pos.setX(screen_rect.width() - self.width())
            if target_pos.y() < 0:
                target_pos.setY(0)
            if target_pos.y() + self.height() > screen_rect.height():
                target_pos.setY(screen_rect.height() - self.height())
            self.move(target_pos)
