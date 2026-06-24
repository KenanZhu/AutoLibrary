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
import time

import requests
import qtawesome as qta

from PySide6.QtCore import (
    QProcess,
    Qt,
    QTimer,
    Signal,
    Slot
)
from PySide6.QtGui import (
    QCloseEvent
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
    QStyleFactory,
    QWidget
)

import managers.config.ConfigManager as ConfigManager
from managers.bulletin.BulletinManager import instance as bulletinInstance
from managers.log.LogManager import instance as logInstance
from managers.theme.ThemeManager import(
    getActiveStyle,
    setActiveStyle,
    instance as themeInstance
)

from gui.ALWidgetMixin import CenterOnParentMixin
from gui.resources.ui.Ui_ALSettingsWidget import Ui_ALSettingsWidget
from interfaces.ConfigProvider import (
    CfgKey,
    ConfigProvider
)


def _applyCustomTheme(
    name: str,
    fallback_theme: str = "system"
) -> bool:

    if not name:
        themeInstance().clearTheme(fallback_theme)
        return True
    try:
        themeInstance().applyTheme(name)
        return True
    except Exception as e:
        logInstance().getLogger("ALSettingsWidget").warning(
            f"无法应用自定义主题 '{name}'，回退到 {fallback_theme} 外观: {e}"
        )
        themeInstance().clearTheme(fallback_theme)
        return False

def _themeToReadable(
    need_theme: str
) -> str:

    if need_theme == "dark":
        return "深色"
    elif need_theme == "light":
        return "浅色"
    elif need_theme == "both":
        return "所有"
    else:
        return "未知"

def _restartApp(
):

    QApplication.instance().quit()
    QProcess.startDetached(sys.executable, sys.argv)


class ALSettingsWidget(CenterOnParentMixin, QWidget, Ui_ALSettingsWidget):

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
        self.__original_bulletin_url: str = ""
        self.__original_bulletin_auto_fetch: bool = False
        self.__original_bulletin_sync_interval: int = 10

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()
        self.loadSettings()

    def closeEvent(
        self,
        event: QCloseEvent
    ):

        self.settingsWidgetIsClosed.emit()
        super().closeEvent(event)

    def modifyUi(
        self
    ):

        self.setWindowFlags(Qt.WindowType.Window)
        self.setNavigationIcons()
        color = QApplication.instance().palette().color(
            QApplication.instance().palette().ColorRole.WindowText
        ).name()
        self.ImportCustomThemeButton.setIcon(qta.icon("fa6s.plus", color=color))
        self.ImportCustomThemeButton.setText("")
        self.RemoveCustomThemeButton.setIcon(qta.icon("fa6s.minus", color=color))
        self.RemoveCustomThemeButton.setText("")
        self.CustomThemeInfoLabel.setTextFormat(Qt.TextFormat.RichText)
        self.CustomThemeInfoLabel.setStyleSheet(
            "border: 1px solid palette(mid);"\
            "border-radius: 2px;"\
            "padding: 5px;"
        )
        self.NavigationList.setCurrentRow(0)
        self.NavigationList.currentRowChanged.connect(self.PageStack.setCurrentIndex)
        self.populateStyles()
        self.populateCustomThemes()

    def setNavigationIcons(
        self
    ):

        app : QApplication | None = QApplication.instance()
        color = app.palette().color(app.palette().ColorRole.WindowText).name()
        item0 = self.NavigationList.item(0)
        if item0:
            item0.setIcon(qta.icon("fa6s.palette", color=color))
        item1 = self.NavigationList.item(1)
        if item1:
            item1.setIcon(qta.icon("fa6s.bullhorn", color=color))

    def populateStyles(
        self
    ):

        self.StyleComboBox.clear()
        self.StyleComboBox.addItems(QStyleFactory.keys())

    def populateCustomThemes(
        self
    ):

        self.CustomThemeComboBox.blockSignals(True)
        self.CustomThemeComboBox.clear()
        self.CustomThemeComboBox.addItem("默认", "")
        self.__theme_cache = {}
        themes = themeInstance().listThemes()
        for t in themes:
            name = t.get("name", "")
            file = t.get("file", name)
            author = t.get("author", "")
            if name:
                self.__theme_cache[file] = t
                self.CustomThemeComboBox.addItem(name, file)
        self.CustomThemeComboBox.blockSignals(False)

    def connectSignals(
        self
    ):

        self.ImportCustomThemeButton.clicked.connect(self.onImportCustomThemeButtonClicked)
        self.RemoveCustomThemeButton.clicked.connect(self.onRemoveCustomThemeButtonClicked)
        self.CustomThemeComboBox.currentIndexChanged.connect(self.onCustomThemeComboBoxChanged)
        self.ResetCustomThemeButton.clicked.connect(self.onResetCustomThemeButtonClicked)
        self.BulletinTestButton.clicked.connect(self.onBulletinTestButtonClicked)
        self.CancelButton.clicked.connect(self.onCancelButtonClicked)
        self.ApplyButton.clicked.connect(self.onApplyButtonClicked)
        self.ConfirmButton.clicked.connect(self.onConfirmButtonClicked)

    def loadSettings(
        self
    ):

        theme = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.THEME, "system")
        style = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.STYLE, "Fusion")
        custom_theme = self.__cfg_mgr.get(CfgKey.GLOBAL.APPEARANCE.CUSTOM_THEME, "")
        self.__original_theme = theme
        self.__original_custom_theme = custom_theme
        self.__original_style = getActiveStyle()
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
        if custom_theme:
            idx = self.CustomThemeComboBox.findData(custom_theme)
            if idx >= 0:
                self.CustomThemeComboBox.setCurrentIndex(idx)
        self.updateCustomThemeInfo()
        self.updateCustomThemeStatus()

        bulletin_mgr = bulletinInstance()
        self.__original_bulletin_url = bulletin_mgr.serverUrl()
        self.__original_bulletin_auto_fetch = bulletin_mgr.autoFetch()
        self.__original_bulletin_sync_interval = bulletin_mgr.syncInterval()
        self.BulletinServerUrlEdit.setText(self.__original_bulletin_url)
        self.BulletinAutoFetchCheck.setChecked(self.__original_bulletin_auto_fetch)
        self.BulletinSyncIntervalSpin.setValue(self.__original_bulletin_sync_interval)

    def updateCustomThemeInfo(
        self
    ):

        file = self.CustomThemeComboBox.currentData()
        if not file:
            self.CustomThemeInfoLabel.setText("")
            return
        t = self.__theme_cache.get(file)
        if t:
            name = t.get("name", "未知")
            author = t.get("author", "未知作者")
            need_theme = t.get("need_theme", "both")
            brief = t.get("brief", "没有相关简介")
            self.CustomThemeInfoLabel.setText(
                f"<b>{name}</b> - 适用于 <i>{_themeToReadable(need_theme)}</i> 主题<br>"
                f"作者：{author}<br><br>"
                f"{brief}"
            )
        else:
            self.CustomThemeInfoLabel.setText("")

    def updateCustomThemeStatus(
        self
    ):

        file = self.CustomThemeComboBox.currentData()
        t = self.__theme_cache.get(file) if file else None
        name = t.get("name", "") if t else ""
        if name:
            self.CustomThemeStatusLabel.setText(f"当前使用 {name} 主题。")
        else:
            self.CustomThemeStatusLabel.setText("当前使用 默认 主题。")

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
        custom_theme = self.CustomThemeComboBox.currentData() or ""
        if not custom_theme:
            custom_theme = ""
        return theme, style, custom_theme

    def clearBulletinTestStatus(
        self
    ):

        self.BulletinTestStatusLabel.setText("")
        self.BulletinTestStatusLabel.setStyleSheet("")

    def saveBulletinSettings(
        self
    ):

        url = self.BulletinServerUrlEdit.text().strip()
        auto_fetch = self.BulletinAutoFetchCheck.isChecked()
        sync_interval = self.BulletinSyncIntervalSpin.value()
        if sync_interval < 1:
            sync_interval = 5
        self.__cfg_mgr.set(CfgKey.GLOBAL.BULLETIN.SERVER_URL, url)
        self.__cfg_mgr.set(CfgKey.GLOBAL.BULLETIN.AUTO_FETCH, auto_fetch)
        self.__cfg_mgr.set(CfgKey.GLOBAL.BULLETIN.SYNC_INTERVAL, sync_interval)
        self.__original_bulletin_url = url
        self.__original_bulletin_auto_fetch = auto_fetch
        self.__original_bulletin_sync_interval = sync_interval

    def saveAndApply(
        self
    ):

        theme, style, custom_theme = self.collectSettings()
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.STYLE, style)
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.CUSTOM_THEME, custom_theme)
        setActiveStyle(style)
        if not _applyCustomTheme(custom_theme, theme):
            self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.CUSTOM_THEME, "")
        self.syncRadioFromNeedTheme(custom_theme)
        theme, _, _ = self.collectSettings()
        self.__cfg_mgr.set(CfgKey.GLOBAL.APPEARANCE.THEME, theme)
        self.setNavigationIcons()
        self.updateCustomThemeStatus()
        self.updateCustomThemeInfo()
        self.__original_theme = theme
        self.__original_custom_theme = custom_theme if custom_theme else ""
        self.__original_style = getActiveStyle()

        self.saveBulletinSettings()

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
    def onRemoveCustomThemeButtonClicked(
        self
    ):

        file = self.CustomThemeComboBox.currentData()
        if not file:
            QMessageBox.information(
                self,
                "提示 - AutoLibrary",
                "请先选择一个主题。"
            )
            return
        t = self.__theme_cache.get(file)
        name = t.get("name", file) if t else file
        reply = QMessageBox.question(
            self,
            "删除主题 - AutoLibrary",
            f"确定要删除主题 \"{name}\" 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        try:
            themeInstance().removeTheme(file)
            self.populateCustomThemes()
            self.CustomThemeComboBox.setCurrentIndex(0)
            self.updateCustomThemeStatus()
            self.updateCustomThemeInfo()
        except Exception as e:
            QMessageBox.warning(
                self,
                "删除失败 - AutoLibrary",
                f"无法删除主题：{e}"
            )

    @Slot()
    def onImportCustomThemeButtonClicked(
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
            file_id = themeInstance().importTheme(file_path)
            self.populateCustomThemes()
            idx = self.CustomThemeComboBox.findData(file_id)
            if idx >= 0:
                self.CustomThemeComboBox.setCurrentIndex(idx)
            self.updateCustomThemeStatus()
            self.updateCustomThemeInfo()
        except Exception as e:
            QMessageBox.warning(
                self,
                "导入失败 - AutoLibrary",
                f"无法导入主题文件：{e}"
            )

    @Slot()
    def onCustomThemeComboBoxChanged(
        self,
        index: int
    ):

        self.updateCustomThemeInfo()

    @Slot()
    def onResetCustomThemeButtonClicked(
        self
    ):

        self.CustomThemeComboBox.blockSignals(True)
        if self.__original_custom_theme:
            idx = self.CustomThemeComboBox.findData(self.__original_custom_theme)
            if idx >= 0:
                self.CustomThemeComboBox.setCurrentIndex(idx)
            else:
                self.CustomThemeComboBox.setCurrentIndex(0)
        else:
            self.CustomThemeComboBox.setCurrentIndex(0)
        self.CustomThemeComboBox.blockSignals(False)
        if self.__original_theme == "light":
            self.LightThemeRadio.setChecked(True)
        elif self.__original_theme == "dark":
            self.DarkThemeRadio.setChecked(True)
        else:
            self.SystemThemeRadio.setChecked(True)
        self.updateCustomThemeInfo()
        self.updateCustomThemeStatus()

    @Slot()
    def onBulletinTestButtonClicked(
        self
    ):

        url = self.BulletinServerUrlEdit.text().strip()
        if not url:
            self.BulletinTestStatusLabel.setText("请先输入服务器地址。")
            self.BulletinTestStatusLabel.setStyleSheet("color: red;")
            return
        if hasattr(self, '__bulletin_test_worker') and self.__bulletin_test_worker is not None:
            return
        self.BulletinTestButton.setEnabled(False)
        self.BulletinTestStatusLabel.setText("正在测试连接...")
        self.BulletinTestStatusLabel.setStyleSheet("")
        self.__bulletin_test_t0 = time.monotonic()
        from gui.ALBulletinDialog import ALBulletinFetchWorker
        api_url = url.rstrip("/") + "/bulletins"
        self.__bulletin_test_worker = ALBulletinFetchWorker(
            self, api_url, {"date": "", "time": "", "range_hour": "1"}
        )
        self.__bulletin_test_worker.fetchWorkerIsFinished.connect(
            self.__onBulletinTestFetched
        )
        self.__bulletin_test_worker.fetchWorkerFinishedWithError.connect(
            self.__onBulletinTestError
        )
        self.__bulletin_test_worker.start()

    @Slot(dict)
    def __onBulletinTestFetched(
        self,
        data: dict
    ):

        self.__bulletin_test_worker.fetchWorkerIsFinished.disconnect(
            self.__onBulletinTestFetched
        )
        self.__bulletin_test_worker.fetchWorkerFinishedWithError.disconnect(
            self.__onBulletinTestError
        )
        self.__bulletin_test_worker.deleteLater()
        self.__bulletin_test_worker = None
        elapsed_ms = (time.monotonic() - self.__bulletin_test_t0) * 1000
        self.BulletinTestStatusLabel.setText(
            f"连接成功！响应延迟 {elapsed_ms:.0f} ms"
        )
        self.BulletinTestStatusLabel.setStyleSheet("color: green;")
        self.BulletinTestButton.setEnabled(True)
        QTimer.singleShot(3000, self.clearBulletinTestStatus)

    @Slot(str)
    def __onBulletinTestError(
        self,
        error_message: str
    ):

        self.__bulletin_test_worker.fetchWorkerIsFinished.disconnect(
            self.__onBulletinTestFetched
        )
        self.__bulletin_test_worker.fetchWorkerFinishedWithError.disconnect(
            self.__onBulletinTestError
        )
        self.__bulletin_test_worker.deleteLater()
        self.__bulletin_test_worker = None
        self.BulletinTestStatusLabel.setText(f"连接失败：{error_message}")
        self.BulletinTestStatusLabel.setStyleSheet("color: red;")
        self.BulletinTestButton.setEnabled(True)

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

        self.onApplyButtonClicked()
        self.close()
