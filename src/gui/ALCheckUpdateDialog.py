# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout
)


class ALCheckUpdateDialog(QDialog):
    """
        Dialog for showing update check result.

        Supports two layouts:
        - has_update=True : version comparison with green text + action buttons
        - has_update=False: "already up-to-date" message + close button
    """

    def __init__(
        self,
        parent=None,
        has_update: bool = False,
        current_version: str = "",
        latest_version: str = "",
        tag_name: str = "",
        html_url: str = ""
    ):

        super().__init__(parent)
        self.__has_update = has_update
        self.__html_url = html_url
        self.__current_version = current_version
        self.__latest_version = latest_version
        self.__tag_name = tag_name

        self.modifyUi()
        self.connectSignals()

    def modifyUi(
        self
    ):

        self.setWindowTitle("检查更新 - AutoLibrary")
        self.setMinimumWidth(360)
        Layout = QVBoxLayout(self)
        Layout.setSpacing(12)
        Layout.setContentsMargins(20, 20, 20, 20)
        if self.__has_update:
            self.buildUpdateAvailableUi(Layout)
        else:
            self.buildUpToDateUi(Layout)

    def buildUpdateAvailableUi(
        self,
        layout: QVBoxLayout
    ):

        TitleLabel = QLabel()
        TitleLabel.setStyleSheet(
            "font-size: 14px;"
            "font-weight: bold;"
        )
        TitleLabel.setTextFormat(Qt.TextFormat.RichText)
        TitleLabel.setText(
            f"检测到新版本: "
            f"<span>{self.__current_version}</span> "
            f"<span>&gt;</span> "
            f"<span style='color: green; font-weight: bold;'>{self.__latest_version}</span>"
        )
        layout.addWidget(TitleLabel)
        InfoLabel = QLabel()
        InfoLabel.setTextFormat(Qt.TextFormat.RichText)
        InfoLabel.setWordWrap(True)
        InfoLabel.setText(
            f"最新版本: <b>{self.__tag_name}</b><br>"
        )
        InfoLabel.setOpenExternalLinks(True)
        layout.addWidget(InfoLabel)
        layout.addSpacing(8)
        self.__button_box = QDialogButtonBox()
        self.__btn_github = self.__button_box.addButton(
            "前往 GitHub",
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.__btn_github.setMinimumWidth(100)
        self.__btn_github.setMaximumWidth(100)
        self.__btn_github.setMinimumHeight(25)
        self.__btn_github.setMaximumHeight(25)
        self.__btn_download = self.__button_box.addButton(
            "官网下载",
            QDialogButtonBox.ButtonRole.ActionRole
        )
        self.__btn_download.setMinimumWidth(80)
        self.__btn_download.setMaximumWidth(80)
        self.__btn_download.setMinimumHeight(25)
        self.__btn_download.setMaximumHeight(25)
        self.__btn_cancel = self.__button_box.addButton(
            "取消",
            QDialogButtonBox.ButtonRole.RejectRole
        )
        self.__btn_cancel.setMinimumWidth(80)
        self.__btn_cancel.setMaximumWidth(80)
        self.__btn_cancel.setMinimumHeight(25)
        self.__btn_cancel.setMaximumHeight(25)
        layout.addWidget(self.__button_box)

    def buildUpToDateUi(
        self,
        layout: QVBoxLayout
    ):

        TitleLabel = QLabel()
        TitleLabel.setStyleSheet(
            "font-size: 14px;"
            "font-weight: bold;"
        )
        TitleLabel.setText(f"已是最新版本 !")
        layout.addWidget(TitleLabel)
        InfoLabel = QLabel()
        InfoLabel.setText(
            f"当前版本: <b>{self.__current_version}</b><br>"
        )
        layout.addWidget(InfoLabel)
        layout.addStretch()
        self.__button_box = QDialogButtonBox()
        self.__btn_close = self.__button_box.addButton(
            "确定",
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.__btn_close.setMinimumWidth(80)
        self.__btn_close.setMaximumWidth(80)
        self.__btn_close.setMinimumHeight(25)
        self.__btn_close.setMaximumHeight(25)
        layout.addWidget(self.__button_box)

    def connectSignals(
        self
    ):

        if self.__has_update:
            self.__btn_github.clicked.connect(self.onGoToGitHub)
            self.__btn_download.clicked.connect(self.onGoToDownload)
            self.__btn_cancel.clicked.connect(self.reject)
        else:
            self.__btn_close.clicked.connect(self.accept)

    def onGoToGitHub(
        self
    ):

        QDesktopServices.openUrl(QUrl(self.__html_url))
        self.accept()

    def onGoToDownload(
        self
    ):

        QDesktopServices.openUrl(
            QUrl("https://www.autolibrary.kenanzhu.com/downloads")
        )
        self.accept()

    @staticmethod
    def showResult(
        parent,
        has_update: bool,
        current_version: str,
        latest_version: str = "",
        tag_name: str = "",
        html_url: str = ""
    ):

        dialog = ALCheckUpdateDialog(
            parent,
            has_update=has_update,
            current_version=current_version,
            latest_version=latest_version,
            tag_name=tag_name,
            html_url=html_url
        )
        dialog.exec()
