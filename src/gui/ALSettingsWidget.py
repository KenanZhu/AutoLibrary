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

def _clearCustomTheme(
    theme: str
):

    app : QApplication | None = QApplication.instance()
    if app:
        app.setStyleSheet("")
    _applyTheme(theme)

def _applyCustomTheme(
    name: str,
    fallback_theme: str = "system"
):

    if not name:
        _clearCustomTheme(fallback_theme)
        return
    try:
        themeInstance().applyTheme(name)
    except Exception:
        _clearCustomTheme(fallback_theme)

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

def _themeToReadable(
    theme: str
) -> str:

    if theme == "dark":
        return "深色"
    elif theme == "light":
        return "浅色"
    elif theme == "both":
        return "所有"
    else:
        return "未知"

class ALSettingsWidget(QWidget, Ui_ALSettingsWidget):

    settingsWidgetIsClosed = Signal()

    def __init__(
        self,
        parent=None
    ):
        super().__init__(parent)
        self.__cfg_mgr: ConfigProvider = ConfigManager.instance()
        self.__original_theme: str = ""
        self.__original_custom_theme: str = ""
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
        self.ThemeInfoLabel.setTextFormat(Qt.TextFormat.RichText)
        self.ThemeInfoLabel.setStyleSheet(
            "border: 1px solid #ccc; " \
            "border-radius: 2px;" \
            "padding: 5px;"
        )

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
        self.ThemeComboBox.currentIndexChanged.connect(self.onThemeComboBoxChanged)
        self.ResetThemeButton.clicked.connect(self.onResetThemeButtonClicked)
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
        self.__original_theme = theme
        self.__original_custom_theme = custom_theme
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
        self.updateThemeInfo()

    def updateThemeStatus(
        self
    ):

        name = self.ThemeComboBox.currentText()
        if name and name != "默认":
            self.QssStatusLabel.setText(f"当前使用 {name} 主题。")
        else:
            self.QssStatusLabel.setText("当前使用 默认 主题。")

    def updateThemeInfo(
        self
    ):

        name = self.ThemeComboBox.currentText()
        if not name or name == "默认":
            self.ThemeInfoLabel.setText("")
            return
        t = self.__theme_cache.get(name)
        if t:
            author = t.get("author", "未知")
            need_theme = t.get("need_theme", "both")
            brief = t.get("brief", "没有相关简介")
            self.ThemeInfoLabel.setText(
                f"<b>{name}</b> - 适用于 <i>{_themeToReadable(need_theme)}</i> 主题<br>"
                f"作者：{author}<br><br>"
                f"{brief}"
            )
        else:
            self.ThemeInfoLabel.setText("")

    def syncRadioFromNeedTheme(
        self,
        name: str
    ):

        t = self.__theme_cache.get(name)
        if t:
            need_theme = t.get("need_theme", "both")
            if need_theme == "light":
                self.LightThemeRadio.setChecked(True)
            elif need_theme == "dark":
                self.DarkThemeRadio.setChecked(True)

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
        if custom_theme == "默认":
            custom_theme = ""
        return theme, style, custom_theme

    def saveAndApply(
        self
    ):

        theme, style, custom_theme = self.collectSettings()
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.STYLE, style)
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.CUSTOM_THEME, custom_theme)
        _applyCustomTheme(custom_theme, theme)
        self.syncRadioFromNeedTheme(custom_theme)
        theme, _, _ = self.collectSettings()
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.THEME, theme)
        _applyTheme(theme)
        self.setNavigationIcons()
        self.updateThemeStatus()
        self.updateThemeInfo()
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
        self.ThemeComboBox.addItem("默认")
        self.__theme_cache = {}
        themes = themeInstance().listThemes()
        for t in themes:
            name = t.get("name", "")
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
            self.updateThemeStatus()
            self.updateThemeInfo()
        except Exception as e:
            QMessageBox.warning(
                self,
                "导入失败 - AutoLibrary",
                f"无法导入主题文件：{e}"
            )

    @Slot()
    def onThemeComboBoxChanged(
        self,
        index: int
    ):

        self.updateThemeInfo()

    @Slot()
    def onResetThemeButtonClicked(
        self
    ):

        self.ThemeComboBox.blockSignals(True)
        self.ThemeComboBox.setCurrentIndex(0)
        self.ThemeComboBox.blockSignals(False)
        if self.__original_theme == "light":
            self.LightThemeRadio.setChecked(True)
        elif self.__original_theme == "dark":
            self.DarkThemeRadio.setChecked(True)
        else:
            self.SystemThemeRadio.setChecked(True)
        self.updateThemeInfo()

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
