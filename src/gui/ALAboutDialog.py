# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import sys
import platform

from PySide6.QtGui import (
    QIcon
)
from PySide6.QtWidgets import (
    QDialog, QApplication
)
from PySide6.QtCore import (
    QTimer, Qt
)

from gui.ALVersionInfo import (
    AL_VERSION, AL_COMMIT_SHA, AL_COMMIT_DATE, AL_BUILD_DATE
)
from gui.Ui_ALAboutDialog import Ui_ALAboutDialog

from gui import AutoLibraryResource


class ALAboutDialog(QDialog, Ui_ALAboutDialog):

    def __init__(
        self,
        parent = None
    ):
        super().__init__(parent)

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()


    def modifyUi(
        self
    ):

        self.LogoIconLabel.setPixmap(QIcon(":/res/icon/icons/AutoLibrary_32x32.ico").pixmap(48, 48))
        info_text = self.generateAboutText()
        self.AboutInfoEdit.setHtml(info_text)
        self.AboutInfoEdit.setTextInteractionFlags(Qt.TextBrowserInteraction)


    def connectSignals(
        self
    ):

        self.CopyButton.clicked.connect(self.copyAboutInfo)


    def generateAboutText(
        self
    ):

        os_info = self.getOSInfo()
        about_text = f"""
<h4>Version Information:</h4>
Version: {AL_VERSION}<br>
Commit SHA: {AL_COMMIT_SHA}<br>
Commit date: {AL_COMMIT_DATE}<br>
Build date: {AL_BUILD_DATE}<br>
Python version: {platform.python_version()}<br>
Qt version: {self.getQtVersion()}<br>

<h4>System Information:</h4>
Processor: {platform.processor()}<br>
Operating system: {os_info['system']}<br>
System version: {os_info['version']}<br>
System architecture: {os_info['architecture']}<br>

<h4>Project Information:</h4>
License: MIT License<br>
Project repository: <a href="https://www.github.com/KenanZhu/AutoLibrary" style="text-decoration: none;">https://www.github.com/KenanZhu/AutoLibrary</a><br>
Project website: <a href="https://www.autolibrary.cv/" style="text-decoration: none;">https://www.autolibrary.cv/</a><br>

<h4>Author Information:</h4>
Developer: KenanZhu<br>
Contact: nanoki_zh@163.com<br>
GitHub: <a href="https://www.github.com/KenanZhu" style="text-decoration: none;">https://www.github.com/KenanZhu</a><br>
"""
        return about_text


    def getOSInfo(
        self
    ):

        system = platform.system()
        version = platform.version()
        architecture = platform.architecture()[0]

        if system == "Windows":
            try:
                version = platform.win32_ver()[1]
            except:
                pass
        elif system == "Darwin":
            try:
                version = platform.mac_ver()[0]
            except:
                pass
        elif system == "Linux":
            try:
                import distro # try to get Linux distro info
                version = f"{distro.name()} {distro.version()}"
            except ImportError:
                pass

        return {
            'system': system,
            'version': version,
            'architecture': architecture
        }


    def getQtVersion(
        self
    ):

        try:
            from PySide6.QtCore import qVersion
            return qVersion()
        except:
            return "Unknown"


    def copyAboutInfo(
        self
    ):

        about_text = self.AboutInfoEdit.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(about_text)
        original_text = self.CopyButton.text()
        self.CopyButton.setText("已复制")
        QTimer.singleShot(2000, lambda: self.CopyButton.setText(original_text))