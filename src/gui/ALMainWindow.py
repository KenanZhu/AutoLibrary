# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import sys
import time
import queue

from PySide6.QtCore import (
    Qt, Signal, Slot, QDir, QFileInfo, QTimer, QThread
)
from PySide6.QtWidgets import (
    QMainWindow, QMenu
)
from PySide6.QtGui import (
    QTextCursor, QCloseEvent, QFont, QIcon
)

from .Ui_ALMainWindow import Ui_ALMainWindow
from .ALConfigWidget import ALConfigWidget

from . import AutoLibraryResource

from operators.AutoLib import AutoLib
from utils.ConfigReader import ConfigReader


class AutoLibWorker(QThread):

    finishedSignal = Signal()
    showTraceSignal = Signal(str)
    showMsgSignal = Signal(str)

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        config_paths: dict
    ):

        super().__init__()

        self.__input_queue = input_queue
        self.__output_queue = output_queue
        self.__config_paths = config_paths
        self.__stopped = False


    def checkTimeAvailable(
        self,
    ) -> bool:

        current_time = time.strftime("%H:%M", time.localtime())
        if current_time >= "23:30" or current_time <= "07:30":
            return False
        return True


    def checkConfigPaths(
        self,
    ) -> bool:

        if not all(
            os.path.exists(path) for path in self.__config_paths.values()
        ):
            self.showTraceSignal.emit(
                "配置文件路径不存在, 请检查配置文件路径是否正确。"
            )
            return False
        return True


    def run(
        self
    ):

        auto_lib = None
        try:
            if not self.checkTimeAvailable():
                self.showTraceSignal.emit(
                    "当前时间不在图书馆开放时间内。\n"\
                    "    请在 07:30 - 23:30 之间尝试"
                )
                return
            if not self.checkConfigPaths():
                return
            self.showTraceSignal.emit("AutoLibrary 开始运行")
            auto_lib = AutoLib(
                self.__input_queue,
                self.__output_queue,
            )
            auto_lib.run(
                ConfigReader(self.__config_paths["system"]),
                ConfigReader(self.__config_paths["users"]),
            )
        except Exception as e:
            self.showTraceSignal.emit(
                f"AutoLibrary 运行时发生异常 : {e}"
            )
        finally:
            if auto_lib:
                auto_lib.close()
            self.showTraceSignal.emit("AutoLibrary 运行结束")
            self.finishedSignal.emit()


    def stop(
        self
    ):

        self.__stopped = True


class ALMainWindow(QMainWindow, Ui_ALMainWindow):

    def __init__(
        self
    ):

        super().__init__()
        self.__class_name = self.__class__.__name__

        self.setupUi(self)
        self.__input_queue = queue.Queue()
        self.__output_queue = queue.Queue()
        script_path = sys.executable
        script_dir = QFileInfo(script_path).absoluteDir()
        self.__config_paths = {
            "system":   QDir.toNativeSeparators(script_dir.absoluteFilePath("system.json")),
            "users": QDir.toNativeSeparators(script_dir.absoluteFilePath("users.json")),
        }
        self.__alConfigWidget = None
        self.__auto_lib_thread = None

        self.modifyUi()
        self.connectSignals()
        self.startMsgPolling()


    def modifyUi(
        self
    ):

        icon = QIcon(":/res/icon/icons/AutoLibrary.ico")
        self.setWindowIcon(icon)
        self.MessageIOTextEdit.setFont(QFont("Courier New", 10))


    def connectSignals(
        self
    ):

        self.ConfigButton.clicked.connect(self.onConfigButtonClicked)
        self.StartButton.clicked.connect(self.onStartButtonClicked)
        self.StopButton.clicked.connect(self.onStopButtonClicked)
        self.SendButton.clicked.connect(self.onSendButtonClicked)
        self.MessageEdit.returnPressed.connect(self.onSendButtonClicked)


    def closeEvent(
        self,
        event: QCloseEvent
    ):

        if self.__timer and self.__timer.isActive():
            self.__timer.stop()
        if self.__alConfigWidget:
            self.__alConfigWidget.close()
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

        self.__timer = QTimer()
        self.__timer.timeout.connect(self.pollMsgQueue)
        self.__timer.start(100)


    def setControlButtons(
        self,
        config_button_enabled: bool,
        start_button_enabled: bool,
        stop_button_enabled: bool
    ):

        self.ConfigButton.setEnabled(config_button_enabled)
        self.StartButton.setEnabled(start_button_enabled)
        self.StopButton.setEnabled(stop_button_enabled)

    @Slot()
    def showMsg(
        self,
        msg: str
    ):

        self.appendToTextEdit(f"[{self.__class_name:<12}] >>> : {msg}")

    @Slot()
    def showTrace(
        self,
        msg: str
    ):

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.appendToTextEdit(f"{timestamp}-[{self.__class_name:<12}] : {msg}")

    @Slot()
    def pollMsgQueue(
        self
    ):

        try:
            while True:
                msg = self.__output_queue.get_nowait()
                self.appendToTextEdit(msg)
        except queue.Empty:
            pass

    @Slot(dict)
    def onConfigWidgetClosed(
        self,
        config_paths: dict
    ):

        if self.__alConfigWidget:
            self.__alConfigWidget.configWidgetCloseSingal.disconnect(self.onConfigWidgetClosed)
            self.__alConfigWidget.deleteLater()
            self.__alConfigWidget = None
        self.ConfigButton.setEnabled(True)
        self.StartButton.setEnabled(True)
        self.StopButton.setEnabled(False)
        self.__config_paths = config_paths

    @Slot()
    def onConfigButtonClicked(
        self
    ):

        if self.__alConfigWidget is None:
            self.__alConfigWidget = ALConfigWidget(
                self,
                self.__config_paths
            )
            self.__alConfigWidget.configWidgetCloseSingal.connect(self.onConfigWidgetClosed)
        self.__alConfigWidget.setWindowFlags(Qt.Window)
        self.__alConfigWidget.setWindowModality(Qt.ApplicationModal)
        self.__alConfigWidget.show()
        self.__alConfigWidget.raise_()
        self.__alConfigWidget.activateWindow()
        self.ConfigButton.setEnabled(False)

    @Slot()
    def onStartButtonClicked(
        self
    ):

        self.setControlButtons(False, False, True)
        if self.__auto_lib_thread is None:
            self.__auto_lib_thread = AutoLibWorker(
                self.__input_queue,
                self.__output_queue,
                self.__config_paths,
            )
            self.__auto_lib_thread.finishedSignal.connect(self.onStopButtonClicked)
            self.__auto_lib_thread.showMsgSignal.connect(self.showMsg)
            self.__auto_lib_thread.showTraceSignal.connect(self.showTrace)
        self.__auto_lib_thread.start()

    @Slot()
    def onStopButtonClicked(
        self
    ):

        if self.__auto_lib_thread:
            self.showTrace("正在停止操作......")
            self.__auto_lib_thread.stop()
            self.__auto_lib_thread.wait()
            self.showTrace("操作已停止")
            self.__auto_lib_thread.showMsgSignal.disconnect(self.showMsg)
            self.__auto_lib_thread.showTraceSignal.disconnect(self.showTrace)
            self.__auto_lib_thread.finishedSignal.disconnect(self.onStopButtonClicked)
            self.__auto_lib_thread.deleteLater()
            self.__auto_lib_thread = None
        self.setControlButtons(True, True, False)

    @Slot()
    def onSendButtonClicked(
        self
    ):

        msg = self.MessageEdit.text().strip()
        if not msg:
            return
        self.showMsg(msg)
        self.MessageEdit.clear()