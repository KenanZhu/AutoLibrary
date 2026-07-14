# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import platform

from PySide6.QtCore import (
    Qt,
    QTimer
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QTabWidget,
    QTextBrowser
)

from gui.ALVersionInfo import (
    AL_VERSION,
    AL_COMMIT_SHA,
    AL_COMMIT_DATE,
    AL_BUILD_DATE
)
from gui.resources.ui.Ui_ALAboutDialog import Ui_ALAboutDialog
from gui.resources import ALResource


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

        self.LogoIconLabel.setPixmap(QIcon(":/res/icons/AutoLibrary_Logo_64.svg").pixmap(48, 48))
        self.TabWidget = QTabWidget()
        self.TabWidget.setDocumentMode(True)
        AboutBrowser = QTextBrowser()
        AboutBrowser.setHtml(self.generateAboutText())
        AboutBrowser.setOpenExternalLinks(True)
        AboutBrowser.setLineWrapMode(QTextBrowser.LineWrapMode.NoWrap)
        AboutBrowser.setTextInteractionFlags(Qt.TextBrowserInteraction)
        browser_font = AboutBrowser.font()
        browser_font.setFamilies(["Courier New", "Consolas", "Menlo", "DejaVu Sans Mono", "monospace"])
        AboutBrowser.setFont(browser_font)
        self.TabWidget.addTab(AboutBrowser, "关于")
        LicenseBrowser = QTextBrowser()
        LicenseBrowser.setHtml(self.generateLicenseText())
        LicenseBrowser.setOpenExternalLinks(True)
        LicenseBrowser.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.TabWidget.addTab(LicenseBrowser, "许可证")
        self.AboutInfoLayout.addWidget(self.TabWidget)

    def connectSignals(
        self
    ):

        self.CopyButton.clicked.connect(self.copyAboutInfo)

    def generateAboutText(
        self
    ) -> str:

        os_info = self.getOSInfo()
        run_on = f"{os_info['system']} {os_info['version']} {os_info['architecture']}"
        selenium_ver = self.getSeleniumVersion()
        about_text = f"""
<b style="font-size:14px;">VERSION: {AL_VERSION}</b><br>
Commit SHA: {AL_COMMIT_SHA}<br>
Commit date: {AL_COMMIT_DATE}<br>
Build date: {AL_BUILD_DATE}<br>
<br>
<b style="font-size:14px;">SYSTEM</b><br>
Running on: {run_on}<br>
Processor: {platform.processor()}<br>
<br>
<b style="font-size:14px;">DEPENDENCIES</b><br>
Python: {platform.python_version()}<br>
Qt(PySide6): {self.getQtVersion()}<br>
Selenium: {selenium_ver}<br>
<br>
<b style="font-size:14px;">PROJECT</b><br>
Website: <a href="https://www.autolibrary.kenanzhu.com" style="text-decoration:none;">https://www.autolibrary.kenanzhu.com</a><br>
Repository: <a href="https://www.github.com/KenanZhu/AutoLibrary" style="text-decoration:none;">https://www.github.com/KenanZhu/AutoLibrary</a><br>
<br>
<b style="font-size:14px;">AUTHOR</b><br>
Developer/Maintainer: KenanZhu<br>
Contact: <a href="mailto:nanoki_zh@163.com">nanoki_zh@163.com</a><br>
GitHub: <a href="https://www.github.com/KenanZhu" style="text-decoration:none;">https://www.github.com/KenanZhu</a><br>
"""
        return about_text

    def generateLicenseText(
        self
    ) -> str:

        return """
<b>MIT License</b>
<p>Copyright &copy; 2025 - 2026 KenanZhu</p>
<p>Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:</p>
<p>The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.</p>
<p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.</p>"""

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

    def getSeleniumVersion(
        self
    ):

        try:
            import selenium
            return selenium.__version__
        except Exception:
            return "Unknown"

    def copyAboutInfo(
        self
    ):

        about_text = self.TabWidget.currentWidget().toPlainText()
        Clipboard = QApplication.clipboard()
        Clipboard.setText(about_text)
        original_text = self.CopyButton.text()
        self.CopyButton.setText("已复制")
        QTimer.singleShot(2000, lambda: self.CopyButton.setText(original_text))
