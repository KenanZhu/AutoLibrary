# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""

from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont, QIcon
)
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPlainTextEdit,
    QDialogButtonBox, QPushButton, QLabel, QApplication, QStyle
)


class ALScriptHighlighter(QSyntaxHighlighter):

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)
        self._rules = []

        keywordFmt = QTextCharFormat()
        keywordFmt.setForeground(QColor("#316BFF"))
        keywordFmt.setFontWeight(QFont.Weight.Bold)
        for kw in ["IF", "ELSE IF", "ELSE", "ENDIF", "END IF",
                    "SET", "PASS", "THEN", ".TRUE.", ".FALSE."]:
            pattern = r"\b" + kw.replace(" ", r"\s+") + r"\b"
            self._rules.append((pattern, keywordFmt))

        opFmt = QTextCharFormat()
        opFmt.setForeground(QColor("#9C27B0"))
        for op in [r"\.EQ\.", r"\.NEQ\.", r"\.BGT\.", r"\.BLT\.",
                   r"\.BGE\.", r"\.BLE\.", r"\.ADD\.", r"\.SUB\."]:
            self._rules.append((op, opFmt))

        varFmt = QTextCharFormat()
        varFmt.setForeground(QColor("#E65100"))
        for var in ["RESERVE_BEGIN_TIME", "RESERVE_END_TIME",
                    "RESERVE_DATE", "USERNAME", "USER_ENABLE",
                    "PRIORITY", "CURRENT_TIME", "CURRENT_DATE"]:
            self._rules.append((r"\b" + var + r"\b", varFmt))

        funcFmt = QTextCharFormat()
        funcFmt.setForeground(QColor("#2E7D32"))
        self._rules.append((r"\bTIME\([^)]+\)", funcFmt))
        self._rules.append((r"\bDATE\([^)]+\)", funcFmt))

        strFmt = QTextCharFormat()
        strFmt.setForeground(QColor("#388E3C"))
        self._rules.append((r"'[^']*'", strFmt))

        numFmt = QTextCharFormat()
        numFmt.setForeground(QColor("#D32F2F"))
        self._rules.append((r"\b\d+\b", numFmt))

        commentFmt = QTextCharFormat()
        commentFmt.setForeground(QColor("#999999"))
        commentFmt.setFontItalic(True)
        self._rules.append((r"//[^\n]*", commentFmt))

    def highlightBlock(
        self,
        text
    ):

        import re
        for pattern, fmt in self._rules:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                start = match.start()
                length = match.end() - match.start()
                self.setFormat(start, length, fmt)


class ALScriptPreviewDialog(QDialog):

    def __init__(
        self,
        parent=None,
        script: str = ""
    ):

        super().__init__(parent)

        self.__fontSize = 13

        self.modifyUi()
        self.connectSignals()

        self._textEdit.setPlainText(script)
        self._highlighter = ALScriptHighlighter(
            self._textEdit.document()
        )


    def modifyUi(
        self
    ):

        self.setWindowTitle("预处理脚本预览 - AutoLibrary")
        self.setMinimumSize(520, 360)

        layout = QVBoxLayout(self)
        toolbarLayout = QHBoxLayout()
        self._zoomInBtn = QPushButton("＋")
        self._zoomInBtn.setFixedSize(30, 25)
        self._zoomOutBtn = QPushButton("－")
        self._zoomOutBtn.setFixedSize(30, 25)
        self._zoomResetBtn = QPushButton(
            QApplication.style().standardIcon(
                QStyle.StandardPixmap.SP_BrowserReload
            ), ""
        )
        self._zoomResetBtn.setFixedSize(30, 25)
        self._zoomResetBtn.setToolTip("重置缩放")
        self._zoomLabel = QLabel(f"{self.__fontSize}px")
        self._zoomLabel.setFixedHeight(25)
        toolbarLayout.addWidget(self._zoomInBtn)
        toolbarLayout.addWidget(self._zoomOutBtn)
        toolbarLayout.addWidget(self._zoomResetBtn)
        toolbarLayout.addWidget(self._zoomLabel)
        toolbarLayout.addStretch()
        self._copyBtn = QPushButton(
            QApplication.style().standardIcon(
                QStyle.StandardPixmap.SP_FileDialogDetailedView
            ), ""
        )
        self._copyBtn.setFixedSize(30, 25)
        self._copyBtn.setToolTip("复制脚本")
        toolbarLayout.addWidget(self._copyBtn)
        layout.addLayout(toolbarLayout)

        self._textEdit = QPlainTextEdit(self)
        self._textEdit.setReadOnly(True)
        self._textEdit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )
        self._textEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
            "  font-size: 13px;"
            "}"
        )
        layout.addWidget(self._textEdit)

        self._btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close
        )
        self._btnBox.button(
            QDialogButtonBox.StandardButton.Close
        ).setText("关闭")
        layout.addWidget(self._btnBox)


    def connectSignals(
        self
    ):

        self._btnBox.rejected.connect(self.reject)
        self._zoomInBtn.clicked.connect(self._onZoomIn)
        self._zoomOutBtn.clicked.connect(self._onZoomOut)
        self._zoomResetBtn.clicked.connect(self._onZoomReset)
        self._copyBtn.clicked.connect(self._onCopy)


    def _onZoomIn(
        self
    ):

        self.__fontSize = min(self.__fontSize + 2, 40)
        self._updateFontSize()


    def _onZoomOut(
        self
    ):

        self.__fontSize = max(self.__fontSize - 2, 8)
        self._updateFontSize()


    def _onZoomReset(
        self
    ):

        self.__fontSize = 13
        self._updateFontSize()


    def _onCopy(
        self
    ):

        clipboard = QApplication.clipboard()
        clipboard.setText(self._textEdit.toPlainText())
        original = self._copyBtn.text()
        self._copyBtn.setText("已复制")
        self._copyBtn.setEnabled(False)
        from PySide6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: (
            self._copyBtn.setText(original),
            self._copyBtn.setEnabled(True)
        ))


    def _updateFontSize(
        self
    ):

        font = self._textEdit.font()
        font.setPointSize(self.__fontSize)
        self._textEdit.setFont(font)
        self._textEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
            f"  font-size: {self.__fontSize}px;"
            "}"
        )
        self._zoomLabel.setText(f"{self.__fontSize}px")
