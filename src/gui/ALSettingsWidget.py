# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import sys

import qtawesome as qta

from PySide6.QtCore import (
    QProcess,
    Qt,
    Signal,
    Slot
)
from PySide6.QtGui import (
    QCloseEvent,
    QShowEvent
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QStyle,
    QStyleFactory,
    QWidget
)

import managers.config.ConfigManager as ConfigManager

from gui.resources.ui.Ui_ALSettingsWidget import Ui_ALSettingsWidget
from interfaces.ConfigProvider import (
    CfgKey,
    ConfigProvider
)


def _clearQss(
):

    app : QApplication | None = QApplication.instance()
    if app:
        app.setStyleSheet("")

def _loadQss(
    file_path: str
) -> str:

    if not file_path or not os.path.isfile(file_path):
        return ""
    try:
        with open(file_path, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""

def _applyQss(
    file_path: str
):

    app : QApplication | None = QApplication.instance()
    if not app:
        return
    qss = _loadQss(file_path)
    if qss:
        app.setStyleSheet(qss)
    else:
        _clearQss()

def _applyTheme(
    theme: str
):

    app : QApplication | None = QApplication.instance()
    if not app:
        return
    if theme == "dark":
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    elif theme == "light":
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    else:
        app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)
    app.setStyle(QStyleFactory.create(app.style().objectName()))

def _restartApp(
):

    QApplication.instance().quit()
    QProcess.startDetached(sys.executable, sys.argv)


class ALSettingsWidget(QWidget, Ui_ALSettingsWidget):

    settingsWidgetIsClosed = Signal()

    def __init__(
        self,
        parent=None
    ):
        super().__init__(parent)
        self.__cfg_mgr: ConfigProvider = ConfigManager.instance()
        self.__original_style: QStyle | None = None

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()
        self.loadSettings()

    def modifyUi(
        self
    ):

        self.setWindowFlags(Qt.WindowType.Window)
        self.NavigationList.setCurrentRow(0)
        self.populateStyles()
        self.setNavigationIcons()

    def setNavigationIcons(
        self
    ):

        app : QApplication | None = QApplication.instance()
        color = app.palette().color(app.palette().ColorRole.WindowText).name()
        item = self.NavigationList.item(0)
        if item:
            item.setIcon(qta.icon("fa5s.palette", color=color))

    def populateStyles(
        self
    ):

        self.StyleComboBox.clear()
        self.StyleComboBox.addItems(QStyleFactory.keys())

    def connectSignals(
        self
    ):

        self.BrowseQssButton.clicked.connect(self.onBrowseQssButtonClicked)
        self.ApplyQssButton.clicked.connect(self.onApplyQssButtonClicked)
        self.ResetQssButton.clicked.connect(self.onResetQssButtonClicked)
        self.CancelButton.clicked.connect(self.onCancelButtonClicked)
        self.ApplyButton.clicked.connect(self.onApplyButtonClicked)
        self.ConfirmButton.clicked.connect(self.onConfirmButtonClicked)

    def showEvent(
        self,
        event: QShowEvent
    ):

        result = super().showEvent(event)
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

    def closeEvent(
        self,
        event: QCloseEvent
    ):

        self.settingsWidgetIsClosed.emit()
        super().closeEvent(event)

    def loadSettings(
        self
    ):

        theme = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.THEME, "system")
        style = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.STYLE, "Fusion")
        custom_qss = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.CUSTOM_QSS, "")
        self.__original_style = QApplication.instance().style()
        if theme == "light":
            self.LightThemeRadio.setChecked(True)
        elif theme == "dark":
            self.DarkThemeRadio.setChecked(True)
        else:
            self.SystemThemeRadio.setChecked(True)
        index = self.StyleComboBox.findText(style)
        if index >= 0:
            self.StyleComboBox.setCurrentIndex(index)
        else:
            self.StyleComboBox.setCurrentIndex(0)
        self.QssPathEdit.setText(custom_qss)
        self.updateQssStatus(custom_qss)

    def updateQssStatus(
        self,
        qss_path: str
    ):

        if qss_path and os.path.isfile(qss_path):
            self.QssStatusLabel.setText(f"已加载自定义样式文件：{qss_path}")
        else:
            self.QssStatusLabel.setText("当前使用程序默认外观。")

    def collectSettings(
        self
    ):

        if self.LightThemeRadio.isChecked():
            theme = "light"
        elif self.DarkThemeRadio.isChecked():
            theme = "dark"
        else:
            theme = "system"
        style = QStyleFactory.create(self.StyleComboBox.currentText())
        custom_qss = self.QssPathEdit.text().strip()
        return theme, style, custom_qss

    def saveAndApply(
        self
    ):

        theme, style, custom_qss = self.collectSettings()
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.THEME, theme)
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.STYLE, style.name())
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.CUSTOM_QSS, custom_qss)
        if custom_qss and os.path.isfile(custom_qss):
            _applyQss(custom_qss)
        else:
            _clearQss()
        _applyTheme(theme)
        self.setNavigationIcons()
        self.updateQssStatus(custom_qss)
        self.__original_style = QApplication.instance().style()

    def maybeRestart(
        self
    ) -> bool:

        reply = QMessageBox.question(
            self,
            "提示 - AutoLibrary",
            "界面风格已修改，需要重启程序才能生效。是否立即重启？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            _restartApp()
            return True
        return False

    @Slot()
    def onBrowseQssButtonClicked(
        self
    ):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择 QSS 样式文件 - AutoLibrary",
            self.QssPathEdit.text(),
            "QSS 样式表文件 (*.qss);;所有文件 (*)"
        )
        if file_path:
            self.QssPathEdit.setText(file_path)

    @Slot()
    def onApplyQssButtonClicked(
        self
    ):

        qss_path = self.QssPathEdit.text().strip()
        if not qss_path:
            QMessageBox.warning(
                self,
                "提示 - AutoLibrary",
                "请先选择或输入 QSS 样式表文件路径。"
            )
            return
        if not os.path.isfile(qss_path):
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"未找到指定的样式文件：\n{qss_path}"
            )
            return
        _applyQss(qss_path)
        self.updateQssStatus(qss_path)

    @Slot()
    def onResetQssButtonClicked(
        self
    ):

        self.QssPathEdit.clear()
        _clearQss()
        if self.LightThemeRadio.isChecked():
            _applyTheme("light")
        elif self.DarkThemeRadio.isChecked():
            _applyTheme("dark")
        else:
            _applyTheme("system")
        self.setNavigationIcons()
        self.updateQssStatus("")

    @Slot()
    def onCancelButtonClicked(
        self
    ):

        self.close()

    @Slot()
    def onApplyButtonClicked(
        self
    ):

        _, style, _ = self.collectSettings()
        style_changed = self.__original_style.name() != style.name()
        self.saveAndApply()
        if style_changed:
            self.maybeRestart()

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        _, style, _ = self.collectSettings()
        style_changed = self.__original_style.name() != style.name()
        self.saveAndApply()
        if style_changed:
            self.maybeRestart()
        self.close()
