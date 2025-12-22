# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""

from enum import Enum

from PySide6.QtCore import (
    Qt, QSize, QCoreApplication, QRect, QPoint
)
from PySide6.QtWidgets import (
    QAbstractScrollArea, QAbstractItemView,
    QTreeWidget, QTreeWidgetItem
)
from PySide6.QtGui import (
     QDragEnterEvent, QDragMoveEvent, QDropEvent
)


class TreeItemType(Enum):

    GROUP = 0
    USER = 1


class ALUserTreeWidget(QTreeWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)

        self.setupUi()
        self.translateUi()


    def setupUi(
        self
    ):

        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"\u5206\u7ec4/\u7528\u6237");
        self.setHeaderItem(__qtreewidgetitem)
        self.setObjectName(u"UserTreeWidget")
        self.setMinimumSize(QSize(230, 0))
        self.setMaximumSize(QSize(250, 16777215))
        self.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)
        self.setTabKeyNavigation(True)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.IgnoreAction)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.setAnimated(True)
        self.setAllColumnsShowFocus(False)
        self.setHeaderHidden(False)
        self.setColumnCount(2)
        self.setColumnWidth(0, 150)
        self.setColumnWidth(1, 20)
        self.header().setCascadingSectionResizes(False)
        self.header().setHighlightSections(False)
        self.header().setProperty(u"showSortIndicator", True)


    def translateUi(
        self
    ):

        ___qtreewidgetitem = self.headerItem()
        ___qtreewidgetitem.setText(1, QCoreApplication.translate("ALConfigWidget", u"\u72b6\u6001", None));


    @staticmethod
    def isDragPositionValid(
        target_rect: QRect,
        drag_pos: QPoint,
    ) -> bool:

        y_offset = drag_pos.y() - target_rect.top()
        valid = (y_offset > target_rect.height()*0.2 and
            y_offset < target_rect.height()*0.8)
        return valid


    def dragEnterEvent(
        self,
        event: QDragEnterEvent
    ):

        super().dragEnterEvent(event)


    def dragMoveEvent(
        self,
        event: QDragMoveEvent
    ):

        super().dragMoveEvent(event)

        source_item = self.currentItem()
        target_item = self.itemAt(event.position().toPoint())
        if source_item is None:
            event.ignore()
            return
        if source_item.type() == TreeItemType.GROUP.value:
            if target_item is not None:
                event.ignore()
                return
        elif source_item.type() == TreeItemType.USER.value:
            if target_item is None:
                event.ignore()
                return
            if target_item.type() != TreeItemType.GROUP.value:
                event.ignore()
                return
            if target_item.checkState(1) == Qt.CheckState.Unchecked:
                event.ignore()
                return
            if not self.isDragPositionValid(
                self.visualItemRect(target_item),
                event.position().toPoint()
            ):
                event.ignore()
                return
        else:
            event.ignore()
            return
        event.acceptProposedAction()


    def dropEvent(
        self,
        event: QDropEvent
    ):

        super().dropEvent(event)

        for item_index in range(self.topLevelItemCount()):
            self.topLevelItem(item_index).setExpanded(True)
        self.setCurrentItem(None)
