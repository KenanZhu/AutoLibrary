# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import requests

from datetime import datetime, timedelta
from typing import Any

from PySide6.QtCore import (
    Qt,
    QThread,
    Signal,
    Slot,
    QTimer
)
from PySide6.QtGui import (
    QFont
)
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
    QWidget
)

from gui.ALStatusLabel import ALStatusLabel
from gui.resources.ui.Ui_ALBulletinDialog import Ui_ALBulletinDialog
from managers.bulletin.BulletinManager import instance as bulletinInstance


class ALBulletinFetchWorker(QThread):
    """
        Worker thread for fetching bulletins from the server.
    """

    fetchWorkerIsFinished = Signal(dict)
    fetchWorkerFinishedWithError = Signal(str)

    def __init__(
        self,
        parent=None,
        request_url: str = "",
        params: dict = None
    ):

        super().__init__(parent)
        self.__request_url = request_url.rstrip("/") if request_url else ""
        self.__params = params or {}

    def run(
        self
    ):

        try:
            response = requests.get(
                self.__request_url, params=self.__params, timeout=5
            )
            response.raise_for_status()
            r = response.json()
            if r.get("code") == 200:
                data = r.get("data", {})
                self.fetchWorkerIsFinished.emit(data)
            else:
                raise Exception(
                    f"服务器返回错误: [{r.get('code', '未知代码')}] {r.get('msg', '未知错误')}"
                )
        except requests.RequestException as e:
            self.fetchWorkerFinishedWithError.emit(f"获取公告数据时发生网络错误: \n{e}")
        except Exception as e:
            self.fetchWorkerFinishedWithError.emit(f"获取公告数据时发生未知错误: \n{e}")


class ALBulletinItemWidget(QWidget):
    """
        Single bulletin item widget for the bulletin list.
    """

    def __init__(
        self,
        parent=None,
        bulletin: dict[str, Any] = None
    ):

        super().__init__(parent)
        self.__bulletin = bulletin.copy() if bulletin else {}
        self.modifyUi()

    def modifyUi(
        self
    ):

        self.ItemWidgetLayout = QVBoxLayout()
        self.ItemWidgetLayout.setSpacing(10)
        self.ItemWidgetLayout.setContentsMargins(10, 5, 10, 5)
        self.BulletinTitleLayout = QHBoxLayout()
        self.BulletinTitleLabel = QLabel(self.__bulletin.get("title", "无标题"))
        titleFont = QFont()
        titleFont.setBold(True)
        self.BulletinTitleLabel.setFont(titleFont)
        self.BulletinTitleLayout.addWidget(self.BulletinTitleLabel)
        if self.__bulletin.get("isNew", False):
            self.NewIndicatorLabel = QLabel("新 !")
            self.NewIndicatorLabel.setStyleSheet(
                "color: #DC0000;"\
                "font-size: 10px;"\
                "font-weight: bold;"\
                "font-style: italic;"
            )
            self.NewIndicatorLabel.setFixedSize(25, 25)
            self.BulletinTitleLayout.addWidget(self.NewIndicatorLabel)
        else:
            self.NewIndicatorLabel = None
        if self.__bulletin.get("isEdited", False):
            self.BulletinIsEditedLabel = QLabel("(已编辑)")
            self.BulletinIsEditedLabel.setStyleSheet(
                "color: #FF9800;"\
                "font-size: 10px;"
            )
            self.BulletinTitleLayout.addWidget(self.BulletinIsEditedLabel)
        self.BulletinTitleLayout.addStretch()
        self.ItemWidgetLayout.addLayout(self.BulletinTitleLayout)
        self.BulletinInfoLayout = QHBoxLayout()
        self.BulletinDateLabel = QLabel()
        try:
            raw_dt = self.__bulletin.get("dateTime", "")
            date_time = datetime.fromisoformat(raw_dt) if raw_dt else datetime.now()
        except (ValueError, TypeError):
            date_time = datetime.now()
        self.BulletinDateLabel.setText(date_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.BulletinDateLabel.setStyleSheet("color: #969696; font-size: 11px;")
        self.BulletinInfoLayout.addWidget(self.BulletinDateLabel)
        self.BulletinAuthorLabel = QLabel(self.__bulletin.get("author", "未知"))
        self.BulletinAuthorLabel.setStyleSheet("color: #969696; font-size: 11px;")
        self.BulletinInfoLayout.addWidget(self.BulletinAuthorLabel)
        self.BulletinInfoLayout.addStretch()
        self.ItemWidgetLayout.addLayout(self.BulletinInfoLayout)
        self.setLayout(self.ItemWidgetLayout)
        self.__bulletin = None

    def markAsRead(
        self
    ):

        if self.NewIndicatorLabel:
            self.NewIndicatorLabel.hide()


class ALBulletinDialog(QDialog, Ui_ALBulletinDialog):
    """
        Bulletin viewer dialog.
    """

    def __init__(
        self,
        parent=None
    ):
        super().__init__(parent)
        self.__sync_timer: QTimer | None = None
        self.__fetch_worker: ALBulletinFetchWorker | None = None
        self.__bulletin_mgr = bulletinInstance()

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()
        self.setupTimer()
        if self.shouldAutoSync():
            self.syncBulletin()

    def modifyUi(
        self
    ):

        self.ALSyncStatusLabel = ALStatusLabel(self)
        self.ALSyncStatusLabel.setFixedSize(30, 30)
        self.SyncLayout.replaceWidget(
            self.SyncStatusPlaceholder, self.ALSyncStatusLabel
        )

        titleFont = QFont()
        titleFont.setBold(True)
        titleFont.setPointSize(15)
        self.BulletinTitleLabel.setFont(titleFont)
        self.BulletinDateLabel.setStyleSheet("color: #969696;")
        self.BulletinAuthorLabel.setStyleSheet("color: #969696;")
        self.BulletinIsEditedLabel.setStyleSheet("color: #FF9800;")
        self.BulletinIsEditedLabel.hide()
        last_time = self.__bulletin_mgr.lastSyncTime()
        if last_time:
            self.setLastSyncTime(last_time)
        self.updateBulletinList(self.__bulletin_mgr.bulletins())

    def shouldAutoSync(
        self
    ) -> bool:

        last = self.__bulletin_mgr.lastSyncTime()
        if last is None:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            interval_min = max(self.__bulletin_mgr.syncInterval()//2, 1)
            threshold = timedelta(minutes=interval_min)
            return (datetime.now().astimezone() - last_dt) > threshold
        except (ValueError, TypeError):
            return True

    def setLastSyncTime(
        self,
        iso_str: str
    ):

        try:
            dt = datetime.fromisoformat(iso_str)
            self.LastSyncDateTimeEdit.setDateTime(dt)
        except (ValueError, TypeError):
            pass

    def connectSignals(
        self
    ):

        self.BulletinListWidget.itemClicked.connect(self.onBulletinListWidgetItemClicked)
        self.SyncButton.clicked.connect(self.syncBulletin)

    def setupTimer(
        self
    ):

        self.__sync_timer = QTimer(self)
        self.__sync_timer.timeout.connect(self.syncBulletin)
        self.__sync_timer.start(self.__bulletin_mgr.syncInterval()*60*1000)

    def updateBulletinList(
        self,
        bulletins: list[dict]
    ):

        self.BulletinListWidget.clear()
        sorted_list = sorted(
            bulletins, key=lambda x: x.get("dateTime", ""), reverse=True
        )
        for bulletin in sorted_list:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, bulletin)
            widget = ALBulletinItemWidget(self, bulletin)
            item.setSizeHint(widget.sizeHint())
            self.BulletinListWidget.addItem(item)
            self.BulletinListWidget.setItemWidget(item, widget)

    def showBulletin(
        self,
        bulletin: dict
    ):

        self.BulletinTitleLabel.setText(bulletin.get("title", "无标题"))
        try:
            raw_dt = bulletin.get("dateTime", "")
            date_time = datetime.fromisoformat(raw_dt) if raw_dt else datetime.now()
        except (ValueError, TypeError):
            date_time = datetime.now()
        self.BulletinDateLabel.setText(date_time.strftime("%Y-%m-%d %H:%M:%S"))
        self.BulletinAuthorLabel.setText(bulletin.get("author", "未知"))
        if bulletin.get("isEdited", False):
            self.BulletinIsEditedLabel.show()
        else:
            self.BulletinIsEditedLabel.hide()
        self.BulletinContentTextBrowser.setHtml(
            "<div style='font-size: 14px;'>{content}</div>".format(
                content=bulletin.get("content", "无内容")
            )
        )

    def clearBulletin(
        self
    ):

        self.BulletinTitleLabel.setText("")
        self.BulletinDateLabel.setText("")
        self.BulletinAuthorLabel.setText("")
        self.BulletinContentTextBrowser.setText("")
        self.BulletinIsEditedLabel.hide()

    def syncBulletin(
        self
    ):

        if self.__fetch_worker is not None:
            return
        self.SyncButton.setEnabled(False)
        self.SyncButton.setText("同步中...")
        self.ALSyncStatusLabel.status = ALStatusLabel.Status.RUNNING
        self.SyncStatusDetailLabel.setText("")
        self.SyncStatusDetailLabel.setStyleSheet("")
        params = self.__bulletin_mgr.getSyncDateTimeAndRange()
        self.__fetch_worker = ALBulletinFetchWorker(
            self, self.__bulletin_mgr.apiUrl(), params
        )
        self.__fetch_worker.fetchWorkerIsFinished.connect(self.onBulletinsFetched)
        self.__fetch_worker.fetchWorkerFinishedWithError.connect(self.onBulletinsFetchError)
        self.__fetch_worker.start()

    @Slot(dict)
    def onBulletinsFetched(
        self,
        data: dict
    ):

        worker = self.sender()
        if worker is not self.__fetch_worker:
            return
        worker.fetchWorkerIsFinished.disconnect(self.onBulletinsFetched)
        worker.fetchWorkerFinishedWithError.disconnect(self.onBulletinsFetchError)
        worker.wait(2000)
        worker.deleteLater()
        self.__fetch_worker = None

        bulletins = data.get("bulletins", [])
        delete_ids = data.get("delete_ids", [])
        merged = self.__bulletin_mgr.updateAndMergeBulletins(bulletins, delete_ids)
        self.__bulletin_mgr.setLastSyncTime(datetime.now().astimezone().isoformat())
        self.SyncButton.setEnabled(True)
        self.SyncButton.setText("同步")
        self.ALSyncStatusLabel.status = ALStatusLabel.Status.SUCCESS
        self.SyncStatusDetailLabel.setText("同步成功")
        self.SyncStatusDetailLabel.setStyleSheet("color: green;")
        QTimer.singleShot(3000, self, self.clearSyncStatus)

        self.setLastSyncTime(self.__bulletin_mgr.lastSyncTime())
        self.updateBulletinList(merged)
        self.clearBulletin()
        interval_ms = self.__bulletin_mgr.syncInterval()*60*1000
        if self.__sync_timer:
            self.__sync_timer.start(interval_ms)

    @Slot(str)
    def onBulletinsFetchError(
        self,
        error_message: str
    ):

        worker = self.sender()
        if worker is not self.__fetch_worker:
            return
        worker.fetchWorkerIsFinished.disconnect(self.onBulletinsFetched)
        worker.fetchWorkerFinishedWithError.disconnect(self.onBulletinsFetchError)
        worker.wait(2000)
        worker.deleteLater()
        self.__fetch_worker = None

        self.SyncButton.setEnabled(True)
        self.SyncButton.setText("重试")
        self.ALSyncStatusLabel.status = ALStatusLabel.Status.FAILURE
        self.SyncStatusDetailLabel.setText("同步失败，请检查网络连接")
        self.SyncStatusDetailLabel.setStyleSheet("color: red;")
        QMessageBox.warning(
            self,
            "警告 - AutoLibrary",
            f"同步失败：{error_message}"
        )
        interval_ms = self.__bulletin_mgr.syncInterval()*60*1000
        if self.__sync_timer:
            self.__sync_timer.start(interval_ms)

    def clearSyncStatus(
        self
    ):

        self.ALSyncStatusLabel.status = ALStatusLabel.Status.WAITING
        self.SyncStatusDetailLabel.setText("")
        self.SyncStatusDetailLabel.setStyleSheet("")

    @Slot(QListWidgetItem)
    def onBulletinListWidgetItemClicked(
        self,
        item: QListWidgetItem
    ):

        if item is None or item.data(Qt.UserRole) is None:
            return
        bulletin = item.data(Qt.UserRole)
        if bulletin.get("isNew", False):
            bulletin["isNew"] = False
            widget = self.BulletinListWidget.itemWidget(item)
            if widget:
                widget.markAsRead()
            item.setData(Qt.UserRole, bulletin)
            self.__bulletin_mgr.markBulletinAsRead(bulletin["id"])
        self.showBulletin(bulletin)
