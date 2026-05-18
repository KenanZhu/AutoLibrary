# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,

    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from autoscript import ALL_VARIABLES


class ALScriptHighlighter(QSyntaxHighlighter):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._rules = []

        keywordFmt = QTextCharFormat()
        keywordFmt.setForeground(QColor("#007ACC"))
        keywordFmt.setFontWeight(QFont.Weight.Bold)
        for kw in ["IF", "ELSE IF", "ELSE", "ENDIF", "END IF",
                    "SET", "PASS", "THEN"]:
            pattern = r"\b" + kw.replace(" ", r"\s+") + r"\b"
            self._rules.append((pattern, keywordFmt))
        opFmt = QTextCharFormat()
        opFmt.setForeground(QColor("#AF00DB"))
        opFmt.setFontWeight(QFont.Weight.Normal)
        for op in [r"\.EQ\.", r"\.NEQ\.", r"\.BGT\.", r"\.BLT\.",
                   r"\.BGE\.", r"\.BLE\.", r"\.ADD\.", r"\.SUB\.",
                   r"\.AND\.", r"\.OR\."]:
            self._rules.append((op, opFmt))
        literalFmt = QTextCharFormat()
        literalFmt.setForeground(QColor("#AF00DB"))
        literalFmt.setFontWeight(QFont.Weight.Bold)
        for lit in [".TRUE.", ".FALSE."]:
            self._rules.append((r"\b" + lit.replace(".", r"\.") + r"\b", literalFmt))
        funcFmt = QTextCharFormat()
        funcFmt.setForeground(QColor("#795E26"))
        funcFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r"\b(?:DATE|TIME)\b", funcFmt))
        varFmt = QTextCharFormat()
        varFmt.setForeground(QColor("#267F99"))
        varFmt.setFontWeight(QFont.Weight.Normal)
        var_names = [name for _, (name, _) in ALL_VARIABLES.items()]
        for var in var_names:
            self._rules.append((r"\b" + var + r"\b", varFmt))
        strFmt = QTextCharFormat()
        strFmt.setForeground(QColor("#A31515"))
        strFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r"'[^']*'", strFmt))
        numFmt = QTextCharFormat()
        numFmt.setForeground(QColor("#098658"))
        numFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r"\b\d+\b", numFmt))
        commentFmt = QTextCharFormat()
        commentFmt.setForeground(QColor("#008000"))
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


class ALAutoScriptEditDialog(QDialog):

    def __init__(
        self,
        parent = None,
        script: str = ""
    ):

        super().__init__(parent)
        self._fontSize = 19

        self.modifyUi()
        self.connectSignals()

        self._textEdit.setPlainText(script)
        self._highlighter = ALScriptHighlighter(
            self._textEdit.document()
        )


    def modifyUi(
        self
    ):

        self.setWindowTitle("AutoScript 编辑 - AutoLibrary")
        self.setMinimumSize(640, 600)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        toolbarLayout = QHBoxLayout()
        self._zoomInBtn = QPushButton("＋")
        self._zoomInBtn.setFixedSize(25, 25)
        self._zoomOutBtn = QPushButton("－")
        self._zoomOutBtn.setFixedSize(25, 25)
        self._zoomResetBtn = QPushButton(
            QApplication.style().standardIcon(
                QStyle.StandardPixmap.SP_BrowserReload
            ), ""
        )
        self._zoomResetBtn.setFixedSize(25, 25)
        self._zoomResetBtn.setToolTip("重置缩放")
        self._zoomLabel = QLabel(f"{self._fontSize}px")
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
        self._copyBtn.setFixedSize(25, 25)
        self._copyBtn.setToolTip("复制脚本")
        toolbarLayout.addWidget(self._copyBtn)
        layout.addLayout(toolbarLayout)
        self._textEdit = QPlainTextEdit(self)
        self._textEdit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )
        self._textEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
           f"  font-size: {self._fontSize}px;"
            "}"
        )
        layout.addWidget(self._textEdit)

        self._createButtonPanel(layout)

        self._btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self._btnBox.button(
            QDialogButtonBox.StandardButton.Ok
        ).setText("保存")
        self._btnBox.button(
            QDialogButtonBox.StandardButton.Cancel
        ).setText("取消")
        layout.addWidget(self._btnBox)

    def _createButtonPanel(
        self,
        parent_layout
    ):


        tab_widget = QTabWidget()
        tab_widget.setMaximumHeight(200)
        basic_widget = QWidget()
        basic_layout = QGridLayout(basic_widget)
        basic_layout.setSpacing(4)
        basic_layout.setContentsMargins(4, 4, 4, 4)
        basic_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        control_buttons = [
            ("IF", "IF()\n    \nEND IF"),
            ("ELSE IF", "ELSE IF()\n    "),
            ("ELSE", "ELSE"),
            ("END IF", "END IF"),
            ("PASS", "PASS"),
        ]
        self._addButtonsToGrid(basic_layout, control_buttons, 0, 0, 5)

        assign_buttons = [
            ("SET", "SET  = "),
        ]
        self._addButtonsToGrid(basic_layout, assign_buttons, 0, 5, 1)

        func_buttons = [
            ("DATE()", "DATE()"),
            ("TIME()", "TIME()"),
        ]
        self._addButtonsToGrid(basic_layout, func_buttons, 1, 0, 2)

        tab_widget.addTab(basic_widget, "基本语法")
        operator_widget = QWidget()
        operator_layout = QGridLayout(operator_widget)
        operator_layout.setSpacing(4)
        operator_layout.setContentsMargins(4, 4, 4, 4)
        operator_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        arithmetic_buttons = [
            (".ADD.", ".ADD."),
            (".SUB.", ".SUB."),
        ]
        self._addButtonsToGrid(operator_layout, arithmetic_buttons, 0, 0, 2)
        compare_buttons = [
            (".EQ.", ".EQ."),
            (".NEQ.", ".NEQ."),
            (".BGT.", ".BGT."),
            (".BLT.", ".BLT."),
            (".BGE.", ".BGE."),
            (".BLE.", ".BLE."),
        ]
        self._addButtonsToGrid(operator_layout, compare_buttons, 1, 0, 6)
        logic_buttons = [
            (".AND.", ".AND."),
            (".OR.", ".OR."),
        ]
        self._addButtonsToGrid(operator_layout, logic_buttons, 2, 0, 2)
        tab_widget.addTab(operator_widget, "运算符")
        literal_widget = QWidget()
        literal_layout = QGridLayout(literal_widget)
        literal_layout.setSpacing(4)
        literal_layout.setContentsMargins(4, 4, 4, 4)
        literal_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        bool_buttons = [
            (".TRUE.", ".TRUE."),
            (".FALSE.", ".FALSE."),
        ]
        self._addButtonsToGrid(literal_layout, bool_buttons, 0, 0, 2)
        hint_buttons = [
            ("字符串", "'文本'"),
            ("数字", "123"),
            ("注释", "// 注释"),
        ]
        self._addButtonsToGrid(literal_layout, hint_buttons, 1, 0, 3)
        tab_widget.addTab(literal_widget, "字面量")
        var_widget = QWidget()
        var_layout = QGridLayout(var_widget)
        var_layout.setSpacing(4)
        var_layout.setContentsMargins(4, 4, 4, 4)
        var_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        var_buttons = [
            (display_name, name) for display_name, (name, _) in ALL_VARIABLES.items()
        ]

        self._addButtonsToGrid(var_layout, var_buttons, 0, 0, 5)
        tab_widget.addTab(var_widget, "变量")
        parent_layout.addWidget(tab_widget)

    def _addButtonsToGrid(
        self,
        grid_layout,
        buttons,
        start_row,
        start_col,
        max_columns
    ):

        col = start_col
        row = start_row

        for btn_text, template in buttons:
            btn = QPushButton(btn_text)
            btn.setProperty("template", template)
            btn.clicked.connect(self._insertTemplate)
            btn.setFixedWidth(100)
            btn.setFixedHeight(30)
            btn.setToolTip(f"插入: {template}")
            grid_layout.addWidget(btn, row, col)

            col += 1
            if col >= start_col + max_columns:
                col = start_col
                row += 1

    @Slot()
    def _insertTemplate(
        self
    ):

        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        template = btn.property("template")
        if not template:
            return
        cursor = self._textEdit.textCursor()
        cursor.insertText(template)

    def connectSignals(
        self
    ):

        self._btnBox.accepted.connect(self.accept)
        self._btnBox.rejected.connect(self.reject)
        self._zoomInBtn.clicked.connect(self.onZoomIn)
        self._zoomOutBtn.clicked.connect(self.onZoomOut)
        self._zoomResetBtn.clicked.connect(self.onZoomReset)
        self._copyBtn.clicked.connect(self.onCopy)


    def getScript(
        self
    ) -> str:

        return self._textEdit.toPlainText()


    def updateFontSize(
        self
    ):

        font = self._textEdit.font()
        font.setPointSize(self._fontSize)
        self._textEdit.setFont(font)
        self._textEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
            f"  font-size: {self._fontSize}px;"
            "}"
        )
        self._zoomLabel.setText(f"{self._fontSize}px")


    @Slot()
    def onZoomIn(
        self
    ):

        self._fontSize = min(self._fontSize + 2, 40)
        self.updateFontSize()


    @Slot()
    def onZoomOut(
        self
    ):

        self._fontSize = max(self._fontSize - 2, 8)
        self.updateFontSize()


    @Slot()
    def onZoomReset(
        self
    ):

        self._fontSize = 13
        self.updateFontSize()


    @Slot()
    def onCopy(
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
