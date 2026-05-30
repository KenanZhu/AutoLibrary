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
    QComboBox,
    QFileDialog,
    QMessageBox,
    QStyleFactory,
    QWidget
)

import managers.config.ConfigManager as ConfigManager
from managers.theme.ThemeManager import instance as themeInstance

from gui.resources.ui.Ui_ALSettingsWidget import Ui_ALSettingsWidget
from interfaces.ConfigProvider import (
    CfgKey,
    ConfigProvider
)


_active_style_name = ""


def _setActiveStyleName(
    name: str
):

    global _active_style_name
    _active_style_name = name

def _clearQss(
):

    app : QApplication | None = QApplication.instance()
    if app:
        app.setStyleSheet("")

def _applyThemeByName(
    name: str
):

    if not name:
        _clearQss()
        return
    try:
        themeInstance().applyTheme(name)
    except Exception:
        _clearQss()

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

    global _active_style_name
    app : QApplication | None = QApplication.instance()
    if not app:
        return
    if theme == "dark":
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    elif theme == "light":
        app.styleHints().setColorScheme(Qt.ColorScheme.Light)
    else:
        app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)
    app.setStyle(QStyleFactory.create(_active_style_name))

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
        self.__original_style: str = ""

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
        self.QssPathEdit.hide()
        self.ApplyQssButton.hide()
        self.ResetQssButton.setText("重置主题")
        self.CustomQssHintLabel.setText("选择一个主题，或导入新的主题文件：")
        self.ThemeComboBox = QComboBox(self.CustomQssGroupBox)
        self.ThemeComboBox.setObjectName("ThemeComboBox")
        self.ThemeComboBox.setMinimumSize(160, 25)
        self.QssPathLayout.insertWidget(0, self.ThemeComboBox)
        self.ThemeStatusLabel = self.QssStatusLabel

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

    def currentStyleKey(
        self
    ) -> str:

        return _active_style_name

    def connectSignals(
        self
    ):

        self.BrowseQssButton.clicked.connect(self.onImportThemeButtonClicked)
        self.ThemeComboBox.currentTextChanged.connect(self.onThemeComboBoxChanged)
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
        custom_theme = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.CUSTOM_THEME, "")
        self.__original_style = self.currentStyleKey()
        if theme == "light":
            self.LightThemeRadio.setChecked(True)
        elif theme == "dark":
            self.DarkThemeRadio.setChecked(True)
        else:
            self.SystemThemeRadio.setChecked(True)
        index = self.StyleComboBox.findText(style)
        if index < 0:
            index = 0
        self.StyleComboBox.setCurrentIndex(index)
        self.populateThemeList()
        if custom_theme:
            idx = self.ThemeComboBox.findText(custom_theme)
            if idx >= 0:
                self.ThemeComboBox.setCurrentIndex(idx)
        self.updateThemeStatus()

    def updateThemeStatus(
        self
    ):

        name = self.ThemeComboBox.currentText()
        if name:
            self.ThemeStatusLabel.setText(f"已加载主题：{name}")
        else:
            self.ThemeStatusLabel.setText("当前使用程序默认外观。")

    def collectSettings(
        self
    ):

        if self.LightThemeRadio.isChecked():
            theme = "light"
        elif self.DarkThemeRadio.isChecked():
            theme = "dark"
        else:
            theme = "system"
        style = self.StyleComboBox.currentText()
        custom_theme = self.ThemeComboBox.currentText()
        return theme, style, custom_theme

    def saveAndApply(
        self
    ):

        theme, style, custom_theme = self.collectSettings()
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.THEME, theme)
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.STYLE, style)
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.CUSTOM_THEME, custom_theme)
        _applyThemeByName(custom_theme)
        _applyTheme(theme)
        self.setNavigationIcons()
        self.updateThemeStatus()
        self.__original_style = self.currentStyleKey()

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

    def populateThemeList(
        self
    ):

        self.ThemeComboBox.blockSignals(True)
        self.ThemeComboBox.clear()
        self.ThemeComboBox.addItem("")
        self.__theme_cache = {}
        themes = themeInstance().listThemes()
        for t in themes:
            name = t.get("name", f"未知主题 {len(self.__theme_cache)+1}")
            if name:
                self.__theme_cache[name] = t
                self.ThemeComboBox.addItem(name)
        self.ThemeComboBox.blockSignals(False)

    @Slot()
    def onImportThemeButtonClicked(
        self
    ):

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "导入主题 - AutoLibrary",
            "",
            "主题文件 (*.altheme *.qss);;所有文件 (*)"
        )
        if not file_path:
            return
        try:
            name = themeInstance().importTheme(file_path)
            self.populateThemeList()
            idx = self.ThemeComboBox.findText(name)
            if idx >= 0:
                self.ThemeComboBox.setCurrentIndex(idx)
            _applyThemeByName(name)
            self.updateThemeStatus()
        except Exception as e:
            QMessageBox.warning(
                self,
                "导入失败 - AutoLibrary",
                f"无法导入主题文件：{e}"
            )

    @Slot()
    def onThemeComboBoxChanged(
        self
    ):

        name = self.ThemeComboBox.currentText()
        if name:
            _applyThemeByName(name)
            t = self.__theme_cache.get(name)
            if t:
                need_theme = t.get("need_theme", "both")
                if need_theme == "light":
                    self.LightThemeRadio.setChecked(True)
                elif need_theme == "dark":
                    self.DarkThemeRadio.setChecked(True)
        else:
            _clearQss()
        self.updateThemeStatus()

    @Slot()
    def onResetQssButtonClicked(
        self
    ):

        self.ThemeComboBox.setCurrentIndex(0)
        _clearQss()
        if self.LightThemeRadio.isChecked():
            _applyTheme("light")
        elif self.DarkThemeRadio.isChecked():
            _applyTheme("dark")
        else:
            _applyTheme("system")
        self.setNavigationIcons()
        self.updateThemeStatus()

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
        style_changed = self.__original_style != style
        self.saveAndApply()
        if style_changed:
            self.maybeRestart()

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        _, style, _ = self.collectSettings()
        style_changed = self.__original_style != style
        self.saveAndApply()
        if style_changed:
            self.maybeRestart()
        self.close()
