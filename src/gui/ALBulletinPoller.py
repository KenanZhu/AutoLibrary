# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from datetime import datetime

from PySide6.QtCore import (
    QObject,
    QTimer,
    Signal,
    Slot
)

from gui.ALBulletinDialog import ALBulletinFetchWorker
from managers.bulletin.BulletinManager import instance as bulletinInstance


class ALBulletinPoller(QObject):
    """
        Background bulletin poller.

        Owns the periodic poll timer and the ALBulletinFetchWorker
        lifecycle. Emits signals when new bulletins are detected so
        the owner can show tray notifications without knowing the
        fetch / merge details.
    """

    newBulletinsDetected = Signal(int)

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)
        self.__timer = QTimer(self)
        self.__timer.timeout.connect(self.__poll)
        self.__worker = None
        self.__dialog_open = False
        self.__mgr = bulletinInstance()

    def start(
        self
    ):

        interval_ms = self.__mgr.syncInterval()*60*1000
        self.__timer.start(interval_ms)

    def stop(
        self
    ):

        self.__timer.stop()
        self.__cleanupWorker()

    def restart(
        self
    ):

        self.stop()
        self.start()

    def fetchNow(
        self
    ):

        if self.__worker is not None:
            return
        if self.__dialog_open:
            return
        self.__doFetch()

    def isPolling(
        self
    ) -> bool:

        return self.__timer.isActive()

    def setDialogOpen(
        self,
        open: bool
    ):

        self.__dialog_open = open

    def __doFetch(
        self
    ):

        params = self.__mgr.getSyncDateTimeAndRange()
        self.__worker = ALBulletinFetchWorker(
            self, self.__mgr.apiUrl(), params
        )
        self.__worker.fetchWorkerIsFinished.connect(self.__onFetched)
        self.__worker.fetchWorkerFinishedWithError.connect(self.__onError)
        self.__worker.start()

    @Slot()
    def __poll(
        self
    ):

        if self.__worker is not None:
            return
        if self.__dialog_open:
            return
        self.__doFetch()

    @Slot(dict)
    def __onFetched(
        self,
        data: dict
    ):

        if self.__worker is None:
            return
        self.__worker.fetchWorkerIsFinished.disconnect(self.__onFetched)
        self.__worker.fetchWorkerFinishedWithError.disconnect(self.__onError)
        self.__worker.wait(2000)
        self.__worker.deleteLater()
        self.__worker = None
        old_ids = {b["id"] for b in self.__mgr.bulletins()}
        bulletins = data.get("bulletins", [])
        delete_ids = data.get("delete_ids", [])
        self.__mgr.updateAndMergeBulletins(bulletins, delete_ids)
        self.__mgr.setLastSyncTime(datetime.now().astimezone().isoformat())
        new_ids = {b["id"] for b in bulletins if b["id"] not in old_ids}
        if new_ids:
            self.newBulletinsDetected.emit(len(new_ids))
        interval_ms = self.__mgr.syncInterval()*60*1000
        self.__timer.start(interval_ms)

    @Slot(str)
    def __onError(
        self,
        error_message: str
    ):

        if self.__worker is None:
            return
        self.__worker.fetchWorkerIsFinished.disconnect(self.__onFetched)
        self.__worker.fetchWorkerFinishedWithError.disconnect(self.__onError)
        self.__worker.wait(2000)
        self.__worker.deleteLater()
        self.__worker = None
        interval_ms = self.__mgr.syncInterval()*60*1000
        self.__timer.start(interval_ms)

    def __cleanupWorker(
        self
    ):

        if self.__worker is None:
            return
        try:
            self.__worker.fetchWorkerIsFinished.disconnect()
        except (TypeError, RuntimeError):
            pass
        try:
            self.__worker.fetchWorkerFinishedWithError.disconnect()
        except (TypeError, RuntimeError):
            pass
        self.__worker.wait(2000)
        self.__worker.deleteLater()
        self.__worker = None
