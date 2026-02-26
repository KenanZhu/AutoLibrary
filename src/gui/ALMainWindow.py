# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import queue

from PySide6.QtCore import (
    Qt, Signal, Slot, QTimer, QDir, QUrl,
)
from PySide6.QtWidgets import (
    QMainWindow, QMenu, QSystemTrayIcon, QMessageBox
)
from PySide6.QtGui import (
    QTextCursor, QCloseEvent, QFont, QIcon, QDesktopServices
)

from base.MsgBase import MsgBase

from utils.ConfigManager import ConfigType, instance
from utils.ConfigManager import getValidateAutomationConfigPaths

from gui.resources.ui.Ui_ALMainWindow import Ui_ALMainWindow
from gui.resources import ALResource
from gui.ALConfigWidget import ALConfigWidget
from gui.ALTimerTaskManageWidget import ALTimerTaskManageWidget
from gui.ALAboutDialog import ALAboutDialog
from gui.ALMainWorkers import TimerTaskWorker, AutoLibWorker


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
        self.__cfg_mgr = instance()
        self.__timer_task_queue = queue.Queue()
        self.__config_paths = getValidateAutomationConfigPaths()
        self.__alTimerTaskManageWidget = None
        self.__alConfigWidget = None
        self.__auto_lib_thread = None
        self.__current_timer_task_thread = None
        self.__is_running_timer_task = False

        self.setupUi(self)
        self.modifyUi()
        self.setupTray()
        self.connectSignals()
        self.startMsgPolling()
        self.startTimerTaskPolling()


    def modifyUi(
        self
    ):

        self.icon = QIcon(":/res/icon/icons/AutoLibrary_32x32.ico")
        self.setWindowIcon(self.icon)
        self.MessageIOTextEdit.setFont(QFont("Courier New", 10))
        self.ManualAction.triggered.connect(self.onManualActionTriggered)
        self.AboutAction.triggered.connect(self.onAboutActionTriggered)

        # initialize timer task widget, but not show it
        try:
            self.__alTimerTaskManageWidget = ALTimerTaskManageWidget(self)
        except Exception as e:
            QMessageBox.critical(
                self,
                "错误 - AutoLibrary",
                f"初始化定时任务功能失败: \n{e}"
            )
            self.__alTimerTaskManageWidget = None
            self.TimerTaskManageWidgetButton.setEnabled(False)
            self.TimerTaskManageWidgetButton.setToolTip("定时任务功能初始化失败, 请检查配置文件。")
            return
        self.timerTaskIsRunning.connect(self.__alTimerTaskManageWidget.onTimerTaskIsRunning)
        self.timerTaskIsExecuted.connect(self.__alTimerTaskManageWidget.onTimerTaskIsExecuted)
        self.timerTaskIsError.connect(self.__alTimerTaskManageWidget.onTimerTaskIsError)
        self.__alTimerTaskManageWidget.timerTaskIsReady.connect(self.onTimerTaskIsReady)
        self.__alTimerTaskManageWidget.timerTaskManageWidgetIsClosed.connect(self.onTimerTaskManageWidgetClosed)
        self.__alTimerTaskManageWidget.setWindowFlags(Qt.WindowType.Window|Qt.WindowType.WindowCloseButtonHint)


    def onAboutActionTriggered(
        self
    ):

        about_dialog = ALAboutDialog(self)
        about_dialog.exec()


    def onManualActionTriggered(
        self
    ):

        url = QUrl("https://www.autolibrary.top/manuals")
        QDesktopServices.openUrl(url)


    def setupTray(
        self
    ):

        if not QSystemTrayIcon.isSystemTrayAvailable():
            self.showTraceSignal.emit(
                "系统不支持系统托盘功能, 无法创建系统托盘图标。"
            )
            return
        self.TrayIcon = QSystemTrayIcon(self.icon, self)
        self.TrayIcon.setToolTip("AutoLibrary")

        self.TrayMenu = QMenu()
        self.TrayMenu.addAction("显示主窗口", self.showNormal)
        self.TrayMenu.addAction("显示定时窗口", self.onTimerTaskManageWidgetButtonClicked)
        self.TrayMenu.addAction("最小化到托盘", self.hideToTray)
        self.TrayMenu.addSeparator()
        self.TrayMenu.addAction("退出", self.close)
        self.TrayIcon.setContextMenu(self.TrayMenu)

        self.TrayIcon.setContextMenu(self.TrayMenu)
        self.TrayIcon.activated.connect(self.onTrayIconActivated)
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


    def closeEvent(
        self,
        event: QCloseEvent
    ):

        if self.__msg_queue_timer and self.__msg_queue_timer.isActive():
            self.__msg_queue_timer.stop()
        if self.__timer_task_timer and self.__timer_task_timer.isActive():
            self.__timer_task_timer.stop()
        if self.__is_running_timer_task:
            self.__current_timer_task_thread.wait(2000)
            self.__current_timer_task_thread.deleteLater()
        if self.__alTimerTaskManageWidget:
            self.__alTimerTaskManageWidget.close()
            self.__alTimerTaskManageWidget.deleteLater()
        if self.__alConfigWidget:
            self.__alConfigWidget.close()
            # the config widget is already deleted in the 'self.onConfigWidgetClosed'
        super().closeEvent(event)


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

        if self.__alConfigWidget:
            self.__alConfigWidget.configWidgetIsClosed.disconnect(self.onConfigWidgetClosed)
            self.__alConfigWidget.deleteLater()
            self.__alConfigWidget = None
        self.setControlButtons(True, None, None)

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
            QSystemTrayIcon.MessageIcon.Information,
            1000
        )
        self._showTrace(
            f"定时任务 {timer_task['name']} 执行{'失败' if is_error else '完成'}, uuid: {timer_task['task_uuid']}"
        )
        if not is_error:
            self.timerTaskIsExecuted.emit(timer_task)
        else:
            self.timerTaskIsError.emit(timer_task)

    @Slot()
    def onTimerTaskManageWidgetButtonClicked(
        self
    ):

        self.__alTimerTaskManageWidget.show()
        self.__alTimerTaskManageWidget.raise_()
        self.__alTimerTaskManageWidget.activateWindow()
        self.TimerTaskManageWidgetButton.setEnabled(False)

    @Slot()
    def onConfigButtonClicked(
        self
    ):

        if self.__alConfigWidget is None:
            self.__alConfigWidget = ALConfigWidget(self)
            self.__alConfigWidget.configWidgetIsClosed.connect(self.onConfigWidgetClosed)
        self.__alConfigWidget.show()
        self.__alConfigWidget.raise_()
        self.__alConfigWidget.activateWindow()
        self.ConfigButton.setEnabled(False)

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

    @Slot()
    def onStopButtonClicked(
        self
    ):

        if self.__auto_lib_thread:
            self._showTrace("正在停止操作......")
            self.__auto_lib_thread.wait(2000)
            self._showTrace("操作已停止")
            self.__auto_lib_thread.autoLibWorkerIsFinished.disconnect(self.onStopButtonClicked)
            self.__auto_lib_thread.autoLibWorkerFinishedWithError.disconnect(self.onStopButtonClicked)
            self.__auto_lib_thread.deleteLater()
            self.__auto_lib_thread = None
        self.setControlButtons(None, False, True)

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