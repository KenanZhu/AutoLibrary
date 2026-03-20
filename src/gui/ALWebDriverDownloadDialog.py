# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import threading
from typing import Optional

from PySide6.QtCore import (
    Qt, Slot, QThread, Signal
)
from PySide6.QtWidgets import (
    QDialog, QLabel, QComboBox, QProgressBar,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFrame, QLineEdit
)
from PySide6.QtGui import (
    QCloseEvent
)

from managers.driver.WebDriverManager import (
    instance as webdriver_manager_instance,
    WebDriverManager, WebDriverInfo, WebDriverType
)
from gui.ALStatusLabel import ALStatusLabel


class DownloadWorker(QThread):
    """
        Worker thread for downloading web drivers.
    """

    progress = Signal(float, int, float, str)
    downloadFinished = Signal(object, str)
    downloadError = Signal(str)
    downloadCancelled = Signal()

    def __init__(
        self,
        driver_manager: WebDriverManager,
        driver_info: WebDriverInfo
    ):
        super().__init__()
        self.__driver_manager = driver_manager
        self.__driver_info = driver_info
        self.__driver_path = None
        self.__cancelled = False
        self.__cancel_event = threading.Event()

    def cancel(
        self
    ):
        """
            Cancel the download operation.
        """

        self.__cancelled = True
        self.__cancel_event.set()

    def run(
        self
    ):
        try:
            if self.__cancelled:
                self.downloadCancelled.emit()
                return
            self.__driver_path = self.__driver_manager.installDriver(
                self.__driver_info,
                progress_callback=self.onProgress,
                cancel_event=self.__cancel_event
            )
            if self.__cancelled:
                self.downloadCancelled.emit()
                return
            if self.__driver_path:
                self.downloadFinished.emit(self.__driver_path, "")
            else:
                self.downloadError.emit("下载失败: 未返回有效路径")
        except Exception as e:
            if not self.__cancelled:
                self.downloadError.emit(f"下载失败: {str(e)}")

    def onProgress(
        self,
        downloaded: float,
        total: int,
        speed: float,
        message: str
    ):

        if self.__cancel_event.is_set():
            self.__cancelled = True
        if not self.__cancelled:
            self.progress.emit(downloaded, total, speed, message)

    def stop(
        self
    ):
        """
            Cancel and wait for the thread to finish.
            Must only be called from the main thread.
        """

        self.cancel()
        if not self.isFinished():
            if not self.wait(5000):
                self.terminate()
                self.wait()


class ALWebDriverDownloadDialog(QDialog):

    def __init__(
        self,
        parent: Optional[QDialog] = None,
        driver_dir: str = ""
    ):
        """
            Web driver download dialog.

            Args:
                parent: Parent widget.
                driver_dir: Driver directory path.
        """

        super().__init__(parent)

        self.__driver_dir = driver_dir
        self.__driver_manager: Optional[WebDriverManager] = None
        self.__confirmed = False
        self.__selected_driver_info: Optional[WebDriverInfo] = None
        self.__driver_infos: list[WebDriverInfo] = []
        self.__download_thread: Optional[DownloadWorker] = None

        self.setupUi()
        self.connectSignals()
        self.initializeDriverManager()
        self.refreshDriverList()

    def showEvent(
        self,
        event
    ):

        result = super().showEvent(event)
        if self.parent():
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

    def setupUi(
        self
    ):

        self.setModal(True)
        self.setMaximumHeight(240)
        self.setMinimumHeight(240)
        self.setWindowTitle("浏览器驱动下载 - AutoLibrary")

        self.MainLayout = QVBoxLayout(self)
        self.MainLayout.setContentsMargins(5, 5, 5, 5)
        self.MainLayout.setSpacing(5)

        self.BrowserCountLabel = QLabel("检测到 0 个可用浏览器：")
        self.MainLayout.addWidget(self.BrowserCountLabel)

        self.DriverInfoLayout = QHBoxLayout()
        self.DriverInfoLayout.setSpacing(5)
        self.DriverComboBox = QComboBox()
        self.DriverInfoLayout.addWidget(self.DriverComboBox)
        self.StatusLabel = ALStatusLabel()
        self.StatusLabel.setFixedSize(32, 32)
        self.DriverInfoLayout.addWidget(self.StatusLabel)
        self.MainLayout.addLayout(self.DriverInfoLayout)

        self.DetailLayout = QVBoxLayout()
        self.DetailLayout.setSpacing(5)
        self.DetailLayout.setContentsMargins(5, 5, 5, 5)
        self.BrowserTypeLabel = QLabel("类型：")
        self.DetailLayout.addWidget(self.BrowserTypeLabel)
        self.VersionLabel = QLabel("版本：")
        self.DetailLayout.addWidget(self.VersionLabel)
        self.PathLabel = QLineEdit()
        self.PathLabel.setReadOnly(True)
        self.PathLabel.setText("路径：未安装")
        self.DetailLayout.addWidget(self.PathLabel)
        self.MainLayout.addLayout(self.DetailLayout)

        self.Line = QFrame()
        self.Line.setFrameShape(QFrame.Shape.HLine)
        self.Line.setFrameShadow(QFrame.Shadow.Sunken)
        self.MainLayout.addWidget(self.Line)
        self.ProgressBar = QProgressBar()
        self.ProgressBar.setValue(0)
        self.ProgressBar.setTextVisible(False)
        self.MainLayout.addWidget(self.ProgressBar)
        self.ProgressText = QLabel("")
        self.ProgressText.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.MainLayout.addWidget(self.ProgressText)
        self.ControlLayout = QHBoxLayout()
        self.ControlLayout.setSpacing(8)
        self.ControlLayout.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.RefreshButton = QPushButton("刷新")
        self.RefreshButton.setFixedSize(80, 25)
        self.DownloadButton = QPushButton("下载驱动")
        self.DownloadButton.setFixedSize(80, 25)
        self.DeleteButton = QPushButton("删除驱动")
        self.DeleteButton.setFixedSize(80, 25)
        self.CancelButton = QPushButton("取消")
        self.CancelButton.setFixedSize(80, 25)
        self.ConfirmButton = QPushButton("确认")
        self.ConfirmButton.setFixedSize(80, 25)
        self.ConfirmButton.setEnabled(False)

        self.ControlLayout.addWidget(self.RefreshButton)
        self.ControlLayout.addWidget(self.DownloadButton)
        self.ControlLayout.addWidget(self.DeleteButton)
        self.ControlLayout.addWidget(self.CancelButton)
        self.ControlLayout.addWidget(self.ConfirmButton)
        self.MainLayout.addLayout(self.ControlLayout)


    def connectSignals(
        self
    ):

        self.RefreshButton.clicked.connect(self.onRefreshButtonClicked)
        self.DownloadButton.clicked.connect(self.onDownloadButtonClicked)
        self.DeleteButton.clicked.connect(self.onDeleteButtonClicked)
        self.CancelButton.clicked.connect(self.onCancelButtonClicked)
        self.ConfirmButton.clicked.connect(self.onConfirmButtonClicked)
        self.DriverComboBox.currentIndexChanged.connect(self.onDriverComboBoxChanged)


    def initializeDriverManager(
        self
    ):

        try:
            self.__driver_manager = webdriver_manager_instance(self.__driver_dir)
        except ValueError as e:
            QMessageBox.warning(self, "初始化失败", f"WebDriverManager 初始化失败:\n{str(e)}")
            self.reject()


    def refreshDriverList(
        self
    ):

        if not self.__driver_manager:
            return
        self.__driver_manager.refresh()
        self.__driver_infos = self.__driver_manager.getDriverInfos()
        self.DriverComboBox.clear()
        for driver_info in self.__driver_infos:
            display_text = f"{driver_info.driver_type.value} - {driver_info.browser_version}"
            self.DriverComboBox.addItem(display_text)
        count = len(self.__driver_infos)
        self.BrowserCountLabel.setText(f"检测到 {count} 个可用浏览器：")
        if self.__driver_infos:
            self.onDriverComboBoxChanged(0)


    def onDriverComboBoxChanged(
        self,
        index: int
    ):

        if not self.__driver_infos or index < 0 or index >= len(self.__driver_infos):
            return
        driver_info = self.__driver_infos[index]
        self.updateDriverInfoDisplay(driver_info)
        self.updateButtonStates(driver_info)


    @Slot()
    def onRefreshButtonClicked(
        self
    ):

        self.refreshDriverList()


    @Slot()
    def onDeleteButtonClicked(
        self
    ):

        index = self.DriverComboBox.currentIndex()
        if index < 0 or index >= len(self.__driver_infos):
            return
        driver_info = self.__driver_infos[index]
        if driver_info.driver_status.name != "INSTALLED":
            QMessageBox.information(self, "提示 - AutoLibrary", "该驱动未安装, 无需删除")
            return
        reply = QMessageBox.question(
            self,
            "确认删除 - AutoLibrary",
            f"确定要删除 {driver_info.driver_type.value} 驱动吗 ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return
        try:
            self.__driver_manager.uninstallDriver(driver_info)
            self.refreshDriverList()
            QMessageBox.information(self, "删除成功 - AutoLibrary", "驱动已成功删除")
        except Exception as e:
            QMessageBox.critical(self, "删除失败 - AutoLibrary", f"删除驱动时出错:\n{str(e)}")

    @Slot()
    def onDownloadButtonClicked(
        self
    ):

        index = self.DriverComboBox.currentIndex()
        if index < 0 or index >= len(self.__driver_infos):
            return
        driver_info = self.__driver_infos[index]
        if driver_info.driver_status.name == "INSTALLED":
            return
        self.StatusLabel.status = ALStatusLabel.Status.RUNNING
        self.DownloadButton.setEnabled(False)
        self.RefreshButton.setEnabled(False)
        self.DriverComboBox.setEnabled(False)
        self.ProgressBar.setValue(0)
        self.ProgressText.setText("正在下载驱动...")
        self.__download_thread = DownloadWorker(self.__driver_manager, driver_info)
        self.__download_thread.progress.connect(self.onDownloadProgress)
        self.__download_thread.downloadFinished.connect(self.onDownloadFinished)
        self.__download_thread.downloadError.connect(self.onDownloadError)
        self.__download_thread.downloadCancelled.connect(self.onDownloadCancelled)
        self.__download_thread.finished.connect(self.__onThreadFinished)
        self.__download_thread.start()

    @Slot()
    def onDownloadProgress(
        self,
        downloaded: float,
        total: int,
        speed: float,
        message: str
    ):

        progress = downloaded
        self.ProgressBar.setValue(progress)
        if speed >= 1024:
            speed_text = f"{speed/1024:.1f} MB/s"
        else:
            speed_text = f"{speed:.1f} KB/s"
        progress_text = f"{message}... {downloaded:.1f}% - {speed_text}"
        self.ProgressText.setText(progress_text)

    @Slot()
    def onDownloadFinished(
        self
    ):

        self.ProgressBar.setValue(100)
        self.ProgressText.setText("下载完成 !")
        self.StatusLabel.status = ALStatusLabel.Status.SUCCESS
        index = self.DriverComboBox.currentIndex()
        if 0 <= index < len(self.__driver_infos):
            driver_info = self.__driver_infos[index]
            self.updateDriverInfoDisplay(driver_info)
        self.ConfirmButton.setEnabled(True)
        self.DownloadButton.setEnabled(False)
        self.RefreshButton.setEnabled(True)
        self.DriverComboBox.setEnabled(True)
        self.DeleteButton.setEnabled(True)

    @Slot()
    def onDownloadError(
        self,
        error_message: str
    ):

        self.StatusLabel.status = ALStatusLabel.Status.FAILURE
        QMessageBox.critical(self, "下载失败 - AutoLibrary", error_message)
        self.DownloadButton.setEnabled(True)
        self.RefreshButton.setEnabled(True)
        self.DriverComboBox.setEnabled(True)
        self.CancelButton.setEnabled(True)


    @Slot()
    def onDownloadCancelled(
        self
    ):

        index = self.DriverComboBox.currentIndex()
        if 0 <= index < len(self.__driver_infos):
            driver_info = self.__driver_infos[index]
            self.__driver_manager.cancelDriverDownload(driver_info)
            self.updateDriverInfoDisplay(driver_info)
        self.ProgressText.setText("下载已取消")
        self.ProgressBar.setValue(0)
        self.StatusLabel.status = ALStatusLabel.Status.WAITING
        self.DownloadButton.setEnabled(True)
        self.RefreshButton.setEnabled(True)
        self.DriverComboBox.setEnabled(True)
        self.CancelButton.setEnabled(True)
        self.DeleteButton.setEnabled(False)


    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        index = self.DriverComboBox.currentIndex()
        if index < 0 or index >= len(self.__driver_infos):
            return
        driver_info = self.__driver_infos[index]
        if driver_info.driver_status.name != "INSTALLED":
            return
        self.__selected_driver_info = driver_info
        self.__confirmed = True
        self.accept()


    @Slot()
    def onCancelButtonClicked(
        self
    ):

        if self.__download_thread:
            reply = QMessageBox.question(
                self,
                "确认取消 - AutoLibrary",
                "正在下载中, 确定要取消下载吗 ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.__download_thread.cancel()
        else:
            self.__confirmed = False
            self.__selected_driver_info = None
            self.reject()


    def closeEvent(
        self,
        event: QCloseEvent
    ):

        if self.__download_thread and self.__download_thread.isRunning():
            reply = QMessageBox.question(
                self,
                "确认关闭 - AutoLibrary",
                "驱动正在下载中, 确定要取消并关闭对话框吗 ?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self.__download_thread.stop()
        if not self.__confirmed:
            self.__selected_driver_info = None
        event.accept()
        super().closeEvent(event)

    def __onThreadFinished(
        self
    ):

        if self.__download_thread:
            self.__download_thread.deleteLater()
            self.__download_thread = None


    def getSelectedDriverInfo(
        self
    ) -> Optional[WebDriverInfo]:

        return self.__selected_driver_info


    def updateDriverInfoDisplay(
        self,
        driver_info: WebDriverInfo
    ):

        if driver_info.driver_type == WebDriverType.CHROME:
            driver_type = "Google Chrome"
        elif driver_info.driver_type == WebDriverType.FIREFOX:
            driver_type = "Mozilla Firefox"
        elif driver_info.driver_type == WebDriverType.EDGE:
            driver_type = "Microsoft Edge"
        else:
            driver_type = "未知"
        self.BrowserTypeLabel.setText(f"类型：{driver_type}")
        self.VersionLabel.setText(f"版本：{driver_info.driver_version}")
        if driver_info.driver_path:
            self.PathLabel.setText(str(driver_info.driver_path))
        else:
            self.PathLabel.setText("未安装")
        match driver_info.driver_status.name:
            case "NOT_INSTALLED":
                self.StatusLabel.status = ALStatusLabel.Status.WAITING
            case "INSTALLED":
                self.StatusLabel.status = ALStatusLabel.Status.SUCCESS
            case "DOWNLOADING":
                self.StatusLabel.status = ALStatusLabel.Status.RUNNING
            case "ERROR":
                self.StatusLabel.status = ALStatusLabel.Status.FAILURE


    def updateButtonStates(
        self,
        driver_info: WebDriverInfo
    ):

        if driver_info.driver_status.name == "INSTALLED":
            self.DownloadButton.setEnabled(False)
            self.DeleteButton.setEnabled(True)
            self.ConfirmButton.setEnabled(True)
        else:
            self.DeleteButton.setEnabled(False)
            self.DownloadButton.setEnabled(True)
            self.ConfirmButton.setEnabled(False)
