# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from PySide6.QtCore import (
    QTimer,
    QUrl,
    Qt,
    Signal,
    Slot
)
from PySide6.QtGui import (
    QCloseEvent,
    QDesktopServices,
    QFont,
    QIcon,
    QTextCursor
)
from PySide6.QtWidgets import (
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon
)

from base.MsgBase import MsgBase
from gui.ALAboutDialog import ALAboutDialog
from gui.ALBulletinDialog import ALBulletinDialog
from gui.ALBulletinPoller import ALBulletinPoller
from gui.ALConfigWidget import ALConfigWidget
from gui.ALSettingsWidget import ALSettingsWidget
from gui.ALMainWorkers import (
    AutoLibWorker,
    TimerTaskWorker
)
from gui.ALTimerTaskManageWidget import ALTimerTaskManageWidget
from gui.resources import ALResource
from gui.resources.ui.Ui_ALMainWindow import Ui_ALMainWindow
from managers.bulletin.BulletinManager import instance as bulletinInstance
from managers.config.ConfigUtils import ConfigUtils


class ALMainWindow(MsgBase, QMainWindow, Ui_ALMainWindow):

    # signal : timer task
    timerTaskIsRunning = Signal(dict)
    timerTaskIsExecuted = Signal(dict)
    timerTaskIsError = Signal(dict)

    def __init__(
        self
    ):

        MsgBase.__init__(self, queue.Queue(), queue.Queue())
        QMainWindow.__init__(self)
        self.__timer_task_queue = queue.Queue()
        self.__config_paths = ConfigUtils.getAutomationConfigPaths()
        self.__ALTimerTaskManageWidget = None
        self.__ALConfigWidget = None
        self.__ALSettingsWidget = None
        self.__ALBulletinDialog = None
        self.__bulletin_poller = ALBulletinPoller(self)
        self.__auto_lib_thread = None
        self.__current_timer_task_thread = None
        self.__is_running_timer_task = False

        self.setupUi(self)
        self.modifyUi()
        self.setupTray()
        self.connectSignals()
        self.startMsgPolling()
        self.startTimerTaskPolling()
        self.__bulletin_poller.start()
        if bulletinInstance().autoFetch():
            QTimer.singleShot(1000, self.__bulletin_poller.fetchNow)
        self._showLog("主窗口初始化完成")

    def modifyUi(
        self
    ):

        self.Icon = QIcon(":/res/icons/AutoLibrary_Logo_64.svg")
        self.setWindowIcon(self.Icon)
        self.MessageIOTextEdit.setFont(QFont("Courier New", 10))
        self.ManualAction.triggered.connect(self.onManualActionTriggered)
        self.AboutAction.triggered.connect(self.onAboutActionTriggered)
        self.SettingsAction.triggered.connect(self.onSettingsActionTriggered)
        if hasattr(self, 'BulletinAction'):
            self.BulletinAction.triggered.connect(self.onBulletinActionTriggered)

        # initialize timer task widget, but not show it
        try:
            self.__ALTimerTaskManageWidget = ALTimerTaskManageWidget(self)
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误 - AutoLibrary",
                f"初始化定时任务功能失败: \n{e}"
            )
            self.__ALTimerTaskManageWidget = None
            self.TimerTaskManageWidgetButton.setEnabled(False)
            self.TimerTaskManageWidgetButton.setToolTip("定时任务功能初始化失败, 请检查配置文件。")
            return
        self.timerTaskIsRunning.connect(self.__ALTimerTaskManageWidget.onTimerTaskIsRunning)
        self.timerTaskIsExecuted.connect(self.__ALTimerTaskManageWidget.onTimerTaskIsExecuted)
        self.timerTaskIsError.connect(self.__ALTimerTaskManageWidget.onTimerTaskIsError)
        self.__ALTimerTaskManageWidget.timerTaskIsReady.connect(self.onTimerTaskIsReady)
        self.__ALTimerTaskManageWidget.timerTaskManageWidgetIsClosed.connect(self.onTimerTaskManageWidgetClosed)
        self.__ALTimerTaskManageWidget.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.WindowCloseButtonHint)

    def onAboutActionTriggered(
        self
    ):

        AboutDialog = ALAboutDialog(self)
        AboutDialog.exec()

    def onManualActionTriggered(
        self
    ):

        url = QUrl("https://www.autolibrary.kenanzhu.com/manuals")
        QDesktopServices.openUrl(url)

    def setupTray(
        self
    ):

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self._showTrace("操作系统不支持系统托盘功能, 无法创建系统托盘图标", self.TraceLevel.WARNING)
            return
        self.TrayIcon = QSystemTrayIcon(self.Icon, self)
        self.TrayIcon.setToolTip("AutoLibrary")
        self.TrayMenu = QMenu()
        self.TrayMenu.addAction("显示主窗口", self.showNormal)
        self.TrayMenu.addAction("显示定时窗口", self.onTimerTaskManageWidgetButtonClicked)
        self.TrayMenu.addAction("公告栏", self.onBulletinActionTriggered)
        self.TrayMenu.addAction("最小化到托盘", self.hideToTray)
        self.TrayMenu.addSeparator()
        self.TrayMenu.addAction("退出", self.close)
        self.TrayIcon.setContextMenu(self.TrayMenu)
        self.TrayIcon.activated.connect(self.onTrayIconActivated)
        self.TrayIcon.messageClicked.connect(self.onBulletinActionTriggered)
        self.TrayIcon.show()

    def hideToTray(
        self
    ):

        self.hide()
        self.TrayIcon.showMessage(
            "AutoLibrary",
            "\n已最小化到托盘",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def onTrayIconActivated(
        self,
        reason: QSystemTrayIcon.ActivationReason
    ):

        if reason == QSystemTrayIcon.DoubleClick:
            self.showNormal()

    def connectSignals(
        self
    ):

        self.ConfigButton.clicked.connect(self.onConfigButtonClicked)
        self.TimerTaskManageWidgetButton.clicked.connect(self.onTimerTaskManageWidgetButtonClicked)
        self.StartButton.clicked.connect(self.onStartButtonClicked)
        self.StopButton.clicked.connect(self.onStopButtonClicked)
        self.SendButton.clicked.connect(self.onSendButtonClicked)
        self.MessageEdit.returnPressed.connect(self.onSendButtonClicked)
        self.__bulletin_poller.newBulletinsDetected.connect(self.onBulletinPollerNewBulletins)

    def closeEvent(
        self,
        event: QCloseEvent
    ):

        if not self.isVisible():
            self.showNormal()
            event.ignore()
            return
        if self.__msg_queue_timer and self.__msg_queue_timer.isActive():
            self.__msg_queue_timer.stop()
        if self.__timer_task_timer and self.__timer_task_timer.isActive():
            self.__timer_task_timer.stop()
        if self.__is_running_timer_task:
            self.__current_timer_task_thread.wait(2000)
            self.__current_timer_task_thread.deleteLater()
        if self.__ALTimerTaskManageWidget:
            self.__ALTimerTaskManageWidget.close()
            self.__ALTimerTaskManageWidget.deleteLater()
        if self.__ALConfigWidget:
            self.__ALConfigWidget.close()
            # the config widget is already deleted in the 'self.onConfigWidgetClosed'
        if self.__ALSettingsWidget:
            self.__ALSettingsWidget.close()
            # the settings widget is already deleted in the 'self.onSettingsWidgetClosed'
        if self.__ALBulletinDialog:
            self.__ALBulletinDialog.close()
            # the bulletin dialog is already deleted in the 'self.onBulletinDialogClosed'
        if self.__bulletin_poller:
            self.__bulletin_poller.stop()
        self._showLog("主窗口关闭")
        QMainWindow.closeEvent(self, event)

    def appendToTextEdit(
        self,
        text: str
    ):

        cursor = self.MessageIOTextEdit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text + "\n")
        self.MessageIOTextEdit.setTextCursor(cursor)
        self.MessageIOTextEdit.ensureCursorVisible()
        scrollbar = self.MessageIOTextEdit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def startMsgPolling(
        self
    ):

        self.__msg_queue_timer = QTimer()
        self.__msg_queue_timer.timeout.connect(self.pollMsgQueue)
        self.__msg_queue_timer.start(100)

    def startTimerTaskPolling(
        self
    ):

        self.__timer_task_timer = QTimer()
        self.__timer_task_timer.timeout.connect(self.pollTimerTaskQueue)
        self.__timer_task_timer.start(500)

    def pollTimerTaskQueue(
        self
    ):

        if self.__is_running_timer_task:
            return
        try:
            while not self.__is_running_timer_task:
                timer_task = self.__timer_task_queue.get_nowait()
                self.timerTaskIsRunning.emit(timer_task)
                self.__timer_task_timer.stop()
                self.__is_running_timer_task = True
                self.setControlButtons(None, True, False)
                if not timer_task["silent"]:
                    self.TrayIcon.showMessage(
                        "定时任务 - AutoLibrary",
                        f"\n已开始执行定时任务: \n{timer_task['name']}",
                        QSystemTrayIcon.MessageIcon.Information,
                        1000
                    )
                    self.showNormal()
                self.__current_timer_task_thread = TimerTaskWorker(
                    timer_task,
                    self._input_queue,
                    self._output_queue,
                    self.__config_paths
                )
                self.__current_timer_task_thread.timerTaskWorkerIsFinished.connect(self.onTimerTaskFinished)
                self.__current_timer_task_thread.start()
        except queue.Empty:
            self.__is_running_timer_task = False
            pass

    def setControlButtons(
        self,
        config_button_enabled: bool,
        stop_button_enabled: bool,
        start_button_enabled: bool
    ):

        # if the enable is None, then keep the original state
        if config_button_enabled is not None:
            self.ConfigButton.setEnabled(config_button_enabled)
        if stop_button_enabled is not None:
            self.StopButton.setEnabled(stop_button_enabled)
        if start_button_enabled is not None:
            self.StartButton.setEnabled(start_button_enabled)

    @Slot()
    def pollMsgQueue(
        self
    ):

        try:
            while True:
                msg = self._output_queue.get_nowait()
                self.appendToTextEdit(msg)
        except queue.Empty:
            pass

    @Slot()
    def onTimerTaskManageWidgetClosed(
        self
    ):

        self.TimerTaskManageWidgetButton.setEnabled(True)

    @Slot(dict)
    def onConfigWidgetClosed(
        self
    ):

        if self.__ALConfigWidget:
            self.__ALConfigWidget.configWidgetIsClosed.disconnect(self.onConfigWidgetClosed)
            self.__ALConfigWidget.deleteLater()
            self.__ALConfigWidget = None
        self.__config_paths = ConfigUtils.getAutomationConfigPaths()
        self.setControlButtons(True, None, None)
        self._showLog("配置窗口已关闭,配置文件路径已更新")

    @Slot()
    def onSettingsWidgetClosed(
        self
    ):

        if self.__ALSettingsWidget:
            self.__ALSettingsWidget.settingsWidgetIsClosed.disconnect(self.onSettingsWidgetClosed)
            self.__ALSettingsWidget.deleteLater()
            self.__ALSettingsWidget = None
        self.SettingsAction.setEnabled(True)

    @Slot()
    def onBulletinActionTriggered(
        self
    ):

        self.__bulletin_poller.setDialogOpen(True)
        if self.__ALBulletinDialog is None:
            self.__ALBulletinDialog = ALBulletinDialog(self)
            self.__ALBulletinDialog.finished.connect(self.onBulletinDialogClosed)
        self.__ALBulletinDialog.show()
        self.__ALBulletinDialog.raise_()
        self.__ALBulletinDialog.activateWindow()
        self._showLog("打开公告栏窗口")

    @Slot()
    def onBulletinDialogClosed(
        self
    ):

        if self.__ALBulletinDialog:
            self.__ALBulletinDialog.finished.disconnect(self.onBulletinDialogClosed)
            self.__ALBulletinDialog.deleteLater()
            self.__ALBulletinDialog = None
        self.__bulletin_poller.setDialogOpen(False)

    @Slot(int)
    def onBulletinPollerNewBulletins(
        self,
        count: int
    ):

        if not hasattr(self, "TrayIcon"):
            return
        self.TrayIcon.showMessage(
            "公告栏 - AutoLibrary",
            f"有 {count} 条新公告，点击查看详情。",
            QSystemTrayIcon.MessageIcon.Information,
            3000
        )

    @Slot()
    def onSettingsActionTriggered(
        self
    ):

        if self.__ALSettingsWidget is None:
            self.__ALSettingsWidget = ALSettingsWidget(self)
            self.__ALSettingsWidget.settingsWidgetIsClosed.connect(self.onSettingsWidgetClosed)
        self.__ALSettingsWidget.show()
        self.__ALSettingsWidget.raise_()
        self.__ALSettingsWidget.activateWindow()
        self.SettingsAction.setEnabled(False)
        self._showLog("打开全局设置窗口")

    @Slot(dict)
    def onTimerTaskIsReady(
        self,
        timer_task: dict
    ):

        self.__timer_task_queue.put(timer_task)

    @Slot(dict)
    def onTimerTaskFinished(
        self,
        is_error: bool,
        timer_task: dict
    ):

        self.__current_timer_task_thread.wait(1000)
        self.__current_timer_task_thread.timerTaskWorkerIsFinished.disconnect(self.onTimerTaskFinished)
        self.__current_timer_task_thread.deleteLater()
        self.__current_timer_task_thread = None
        self.setControlButtons(None, False, True)
        self.__is_running_timer_task = False
        self.__timer_task_timer.start(500)
        timer_task["executed"] = True
        self.TrayIcon.showMessage(
            "定时任务 - AutoLibrary",
            f"\n定时任务 '{timer_task['name']}' 执行{'失败' if is_error else '完成'}",
            QSystemTrayIcon.MessageIcon.Warning if is_error else QSystemTrayIcon.MessageIcon.Information,
            1000
        )
        self._showTrace(
            f"定时任务 {timer_task['name']} 执行{'失败' if is_error else '完成'}, uuid: {timer_task['uuid']}"
        )
        if not is_error:
            self.timerTaskIsExecuted.emit(timer_task)
        else:
            self.timerTaskIsError.emit(timer_task)

    @Slot()
    def onTimerTaskManageWidgetButtonClicked(
        self
    ):

        self.__ALTimerTaskManageWidget.show()
        self.__ALTimerTaskManageWidget.raise_()
        self.__ALTimerTaskManageWidget.activateWindow()
        self.TimerTaskManageWidgetButton.setEnabled(False)
        self._showLog("打开定时任务管理窗口")

    @Slot()
    def onConfigButtonClicked(
        self
    ):

        if self.__ALConfigWidget is None:
            self.__ALConfigWidget = ALConfigWidget(self)
            self.__ALConfigWidget.configWidgetIsClosed.connect(self.onConfigWidgetClosed)
        self.__ALConfigWidget.show()
        self.__ALConfigWidget.raise_()
        self.__ALConfigWidget.activateWindow()
        self.ConfigButton.setEnabled(False)
        self._showLog("打开配置窗口")

    @Slot()
    def onStartButtonClicked(
        self
    ):

        self.setControlButtons(None, True, False)
        if self.__auto_lib_thread is None:
            self.__auto_lib_thread = AutoLibWorker(
                self._input_queue,
                self._output_queue,
                self.__config_paths
            )
            self.__auto_lib_thread.autoLibWorkerIsFinished.connect(self.onStopButtonClicked)
            self.__auto_lib_thread.autoLibWorkerFinishedWithError.connect(self.onStopButtonClicked)
        self.__auto_lib_thread.start()
        self._showLog("开始手动执行任务")

    @Slot()
    def onStopButtonClicked(
        self
    ):

        if self.__auto_lib_thread:
            self._showTrace("正在停止操作......", no_log=True)
            self.__auto_lib_thread.wait(2000)
            self._showTrace("操作已停止", no_log=True)
            self.__auto_lib_thread.autoLibWorkerIsFinished.disconnect(self.onStopButtonClicked)
            self.__auto_lib_thread.autoLibWorkerFinishedWithError.disconnect(self.onStopButtonClicked)
            self.__auto_lib_thread.deleteLater()
            self.__auto_lib_thread = None
        self.setControlButtons(None, False, True)
        self._showLog("任务已停止")

    @Slot()
    def onSendButtonClicked(
        self
    ):

        msg = self.MessageEdit.text().strip()
        if not msg:
            return
        self._showMsg(msg)
        self._input_queue.put(msg) # put message to input queue
        self.MessageEdit.clear()