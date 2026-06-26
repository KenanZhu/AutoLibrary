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

from gui.ALBulletinWorker import ALBulletinFetchWorker
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
        self.__stopped = False
        self.__mgr = bulletinInstance()

    def start(
        self
    ):

        self.__stopped = False
        interval_ms = self.__mgr.syncInterval()*60*1000
        self.__timer.start(interval_ms)

    def stop(
        self
    ):

        self.__stopped = True
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

    def __disconnectWorker(
        self,
        worker: ALBulletinFetchWorker
    ):

        try:
            worker.fetchWorkerIsFinished.disconnect(self.__onFetched)
        except (TypeError, RuntimeError):
            pass
        try:
            worker.fetchWorkerFinishedWithError.disconnect(self.__onError)
        except (TypeError, RuntimeError):
            pass

    def __cleanupWorker(
        self
    ):

        if self.__worker is None:
            return
        self.__disconnectWorker(self.__worker)
        self.__worker.wait(500)
        self.__worker.delete()
        self.__worker = None

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

        worker = self.sender()
        if worker is not self.__worker:
            return
        self.__disconnectWorker(worker)
        worker.wait(500)
        worker.delete()
        self.__worker = None
        old_ids = {str(b.get("id", "")) for b in self.__mgr.bulletins()}
        bulletins = data.get("bulletins", [])
        delete_ids = data.get("delete_ids", [])
        self.__mgr.updateAndMergeBulletins(bulletins, delete_ids)
        self.__mgr.setLastSyncTime(datetime.now().astimezone().isoformat())
        delete_id_set = {str(d) for d in delete_ids}
        new_ids = {
            str(b.get("id", ""))
            for b in bulletins
            if str(b.get("id", "")) and str(b.get("id", "")) not in old_ids
        }
        new_ids -= delete_id_set
        if new_ids:
            self.newBulletinsDetected.emit(len(new_ids))
        if not self.__stopped:
            interval_ms = self.__mgr.syncInterval()*60*1000
            self.__timer.start(interval_ms)

    @Slot(str)
    def __onError(
        self,
        error_message: str
    ):

        worker = self.sender()
        if worker is not self.__worker:
            return
        self.__disconnectWorker(worker)
        worker.wait(500)
        worker.delete()
        self.__worker = None
        if not self.__stopped:
            interval_ms = self.__mgr.syncInterval()*60*1000
            self.__timer.start(interval_ms)
