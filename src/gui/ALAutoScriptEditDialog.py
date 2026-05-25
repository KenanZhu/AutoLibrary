# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from copy import deepcopy

from PySide6.QtCore import (
    QDate,
    QSize,
    Qt,
    QTime,
    QTimer,
    Slot
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QSyntaxHighlighter,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from autoscript import (
    createAllVariablesTable,
    createMockTargetData,
    createTargetVarDefs,
    createEngine,
)


class ALScriptHighlighter(QSyntaxHighlighter):
    """
        Syntax highlighter for Lua-based AutoScript.
    """

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._rules = []

        keywordFmt = QTextCharFormat()
        keywordFmt.setForeground(QColor("#569CD6"))
        keywordFmt.setFontWeight(QFont.Weight.Bold)
        for kw in [
            "if", "elseif", "else", "end", "then",
            "and", "or", "not",
            "local", "function", "return", "nil",
        ]:
            self._rules.append((r"\b" + kw + r"\b", keywordFmt))
        boolFmt = QTextCharFormat()
        boolFmt.setForeground(QColor("#4FC1FF"))
        boolFmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((r"\btrue\b", boolFmt))
        self._rules.append((r"\bfalse\b", boolFmt))
        cmpFmt = QTextCharFormat()
        cmpFmt.setForeground(QColor("#C586C0"))
        cmpFmt.setFontWeight(QFont.Weight.Normal)
        for op in [r"==", r"~=", r">=", r"<=", r">", r"<"]:
            self._rules.append((op, cmpFmt))
        arithFmt = QTextCharFormat()
        arithFmt.setForeground(QColor("#C586C0"))
        arithFmt.setFontWeight(QFont.Weight.Normal)
        for op in [r"\+", r"-", r"\*", r"/", r"\.\."]:
            self._rules.append((op, arithFmt))
        funcFmt = QTextCharFormat()
        funcFmt.setForeground(QColor("#DCDCAA"))
        funcFmt.setFontWeight(QFont.Weight.Normal)
        for fn in [ "time", "date", "datenow", "timenow", "dateadd", "timeadd"]:
            self._rules.append((r"\b" + fn + r"\b", funcFmt))
        varFmt = QTextCharFormat()
        varFmt.setForeground(QColor("#9CDCFE"))
        varFmt.setFontWeight(QFont.Weight.Normal)
        var_names = [name for _, (name, _) in createAllVariablesTable().items()]
        for var in var_names:
            self._rules.append((r"\b" + var + r"\b", varFmt))
        strFmt = QTextCharFormat()
        strFmt.setForeground(QColor("#CE9178"))
        strFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r'"[^"]*"', strFmt))
        self._rules.append((r"'[^']*'", strFmt))
        numFmt = QTextCharFormat()
        numFmt.setForeground(QColor("#B5CEA8"))
        numFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r"\b\d+(?:\.\d+)?\b", numFmt))
        commentFmt = QTextCharFormat()
        commentFmt.setForeground(QColor("#6A9955"))
        commentFmt.setFontItalic(True)
        self._rules.append((r"--[^\n]*", commentFmt))

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


class _DebugResultDialog(QDialog):

    def __init__(
        self,
        changes: list,
        parent = None
    ):

        super().__init__(parent)
        self.setWindowTitle("调试运行结果 - AutoLibrary")
        self.setMinimumSize(600, 200)
        layout = QVBoxLayout(self)
        table = QTableWidget(len(changes), 3)
        table.setHorizontalHeaderLabels(["目标变量", "原始数据", "运行后数据"])
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (display_name, name, var_type, before_val, after_val) in enumerate(changes):
            label = f"{display_name}: {name}({var_type})"
            table.setItem(row, 0, QTableWidgetItem(label))
            table.setItem(row, 1, QTableWidgetItem(str(before_val)))
            table.setItem(row, 2, QTableWidgetItem(str(after_val)))
        layout.addWidget(table)
        btnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btnBox.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        btnBox.accepted.connect(self.accept)
        layout.addWidget(btnBox)


class _TabToSpacesEditor(QPlainTextEdit):

    def keyPressEvent(
        self,
        event
    ):

        if event.key() == Qt.Key.Key_Tab:
            self.insertPlainText("    ")
            return
        super().keyPressEvent(event)


class ALAutoScriptEditDialog(QDialog):

    def __init__(
        self,
        parent = None,
        script: str = "",
        mockData: dict = None
    ):

        super().__init__(parent)
        self._fontSize = 21
        self._mockWidgets = {}

        self.setupUi()
        self.connectSignals()
        self.textEdit.setPlainText(script)
        self._highlighter = ALScriptHighlighter(
            self.textEdit.document()
        )
        if mockData:
            self.setMockData(mockData)

    def setupUi(
        self
    ):

        self.setWindowTitle("AutoScript 编辑 - AutoLibrary")
        self.setMinimumSize(660, 600)
        layout = QVBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(3, 3, 3, 3)
        toolbarLayout = QHBoxLayout()
        self.zoomInBtn = QPushButton("＋")
        self.zoomInBtn.setFixedSize(25, 25)
        self.zoomOutBtn = QPushButton("－")
        self.zoomOutBtn.setFixedSize(25, 25)
        self.zoomResetBtn = QPushButton("")
        self.zoomResetBtn.setIcon(QIcon(":/res/icons/Reset.svg"))
        self.zoomResetBtn.setIconSize(QSize(20, 20))
        self.zoomResetBtn.setFixedSize(25, 25)
        self.zoomResetBtn.setToolTip("重置缩放")
        self.zoomLabel = QLabel(f"{self._fontSize}px")
        self.zoomLabel.setFixedHeight(25)
        self.orchBtn = QPushButton("编排")
        self.orchBtn.setFixedHeight(25)
        self.orchBtn.setToolTip("可视化生成 AutoScript 代码并插入到光标位置")
        toolbarLayout.addWidget(self.orchBtn)
        self.debugBtn = QPushButton("▶ 调试运行")
        self.debugBtn.setFixedHeight(25)
        self.debugBtn.setToolTip("使用右侧模拟数据执行脚本，查看目标变量变化")
        toolbarLayout.addWidget(self.debugBtn)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setFixedWidth(1)
        toolbarLayout.addWidget(sep)
        toolbarLayout.addWidget(self.zoomInBtn)
        toolbarLayout.addWidget(self.zoomOutBtn)
        toolbarLayout.addWidget(self.zoomResetBtn)
        toolbarLayout.addWidget(self.zoomLabel)
        toolbarLayout.addStretch()
        self.copyBtn = QPushButton("")
        self.copyBtn.setIcon(QIcon(":/res/icons/Copy.svg"))
        self.copyBtn.setIconSize(QSize(20, 20))
        self.copyBtn.setFixedSize(25, 25)
        self.copyBtn.setToolTip("复制脚本")
        toolbarLayout.addWidget(self.copyBtn)
        layout.addLayout(toolbarLayout)
        self.textEdit = _TabToSpacesEditor(self)
        self.textEdit.setTabStopDistance(40)
        self.textEdit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )
        self.textEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
           f"  font-size: {self._fontSize}px;"
            "}"
        )
        layout.addWidget(self.textEdit)
        self.createButtonPanel(layout)
        self.btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.btnBox.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        self.btnBox.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        layout.addWidget(self.btnBox)

    def createButtonPanel(
        self,
        parent_layout
    ):

        splitter = QSplitter(Qt.Orientation.Horizontal)
        tabWidget = QTabWidget()
        tabWidget.setMaximumHeight(150)
        basicWidget = QWidget()
        basicLayout = QGridLayout(basicWidget)
        basicLayout.setSpacing(4)
        basicLayout.setContentsMargins(4, 4, 4, 4)
        basicLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        controlButtons = [
            ("如果 (if...)", "if  then\n    \nend"),
            ("再如果 (elseif...)", "elseif  then\n    "),
            ("否则 (else)", "else"),
            ("结束 (end)", "end"),
            ("跳过 (pass)", "-- pass"),
        ]
        self.addButtonsToGrid(basicLayout, controlButtons, 0, 0, 3)
        assignButtons = [
            ("赋值 (=)", " = "),
        ]
        self.addButtonsToGrid(basicLayout, assignButtons, 1, 2, 3)
        tabWidget.addTab(basicWidget, "基本语法")
        operatorWidget = QWidget()
        operatorLayout = QGridLayout(operatorWidget)
        operatorLayout.setSpacing(4)
        operatorLayout.setContentsMargins(4, 4, 4, 4)
        operatorLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        arithmeticButtons = [
            ("加 (+)", " + "),
            ("减 (-)", " - "),
        ]
        self.addButtonsToGrid(operatorLayout, arithmeticButtons, 0, 0, 3)
        compareButtons = [
            ("等于 (==)", " == "),
            ("不等于 (~=)", " ~= "),
            ("大于 (>)", " > "),
            ("小于 (<)", " < "),
            ("大于等于 (>=)", " >= "),
            ("小于等于 (<=)", " <= "),
        ]
        self.addButtonsToGrid(operatorLayout, compareButtons, 1, 0, 3)
        logic_buttons = [
            ("且 (and)", " and "),
            ("或 (or)", " or "),
        ]
        self.addButtonsToGrid(operatorLayout, logic_buttons, 2, 0, 3)
        tabWidget.addTab(operatorWidget, "运算符")
        literalWidget = QWidget()
        literalLayout = QGridLayout(literalWidget)
        literalLayout.setSpacing(4)
        literalLayout.setContentsMargins(4, 4, 4, 4)
        literalLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        bool_buttons = [
            ("真 (true)", "true"),
            ("假 (false)", "false"),
        ]
        self.addButtonsToGrid(literalLayout, bool_buttons, 0, 0, 3)
        dateTimeButtons = [
            ("日期", '"2099-01-01"'),
            ("时间", '"00:00"'),
        ]
        self.addButtonsToGrid(literalLayout, dateTimeButtons, 1, 0, 3)
        hintButtons = [
            ("字符串", '"请输入文本"'),
            ("数字", "123"),
            ("注释", "-- 请输入注释"),
        ]
        self.addButtonsToGrid(literalLayout, hintButtons, 2, 0, 3)
        tabWidget.addTab(literalWidget, "字面量")
        varWidget = QWidget()
        varLayout = QGridLayout(varWidget)
        varLayout.setSpacing(4)
        varLayout.setContentsMargins(4, 4, 4, 4)
        varLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        varButtons = [
            (display_name, name) for display_name, (name, _) in createAllVariablesTable().items()
        ]
        self.addButtonsToGrid(varLayout, varButtons, 0, 0, 3)
        tabWidget.addTab(varWidget, "变量")
        funcWidget = QWidget()
        funcLayout = QGridLayout(funcWidget)
        funcLayout.setSpacing(4)
        funcLayout.setContentsMargins(4, 4, 4, 4)
        funcLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        funcButtons = [
            ("datenow()", "datenow()", "返回当前日期的 Unix 时间戳"),
            ("timenow()", "timenow()", "返回当前时间在一天中的分钟数"),
            ("dateadd(d, n)", "dateadd(, )", "日期偏移: dateadd(日期时间戳, 天数)"),
            ("timeadd(t, n)", "timeadd(, )", "时间偏移: timeadd(分钟数, 分钟数)"),
        ]
        for i, (text, template, tooltip) in enumerate(funcButtons):
            btn = QPushButton(text)
            btn.setProperty("template", template)
            btn.clicked.connect(self.insertTemplate)
            btn.setFixedWidth(100)
            btn.setFixedHeight(25)
            btn.setToolTip(tooltip)
            funcLayout.addWidget(btn, i // 2, i % 2)
        tabWidget.addTab(funcWidget, "工具函数")
        mockPanel = self.createMockPanel()
        mockPanel.setMinimumWidth(260)
        splitter.addWidget(tabWidget)
        splitter.addWidget(mockPanel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([530, 530])
        parent_layout.addWidget(splitter)

    def addButtonsToGrid(
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
            btn.clicked.connect(self.insertTemplate)
            btn.setFixedWidth(100)
            btn.setFixedHeight(25)
            btn.setToolTip(f"插入: {template}")
            grid_layout.addWidget(btn, row, col)
            col += 1
            if col >= start_col + max_columns:
                col = start_col
                row += 1

    def createMockPanel(
        self
    ) -> QGroupBox:

        group = QGroupBox("模拟目标数据")
        form = QFormLayout(group)
        form.setSpacing(4)
        form.setContentsMargins(5, 10, 5, 5)
        self._mockWidgets = {}
        mockData = createMockTargetData()
        for name, var_type, key_path, display_name in createTargetVarDefs():
            d = mockData
            for key in key_path:
                d = d[key]
            default = d
            widget = self.makeMockInput(var_type, default)
            label = QLabel(f"{display_name}: {name}({var_type})")
            form.addRow(label, widget)
            self._mockWidgets[name] = (widget, var_type, key_path)
        return group

    def makeMockInput(
        self,
        var_type: str,
        default
    ) -> QWidget:

        if var_type == "String":
            w = QLineEdit()
            w.setText(str(default))
            return w
        if var_type == "Boolean":
            w = QComboBox()
            w.addItems(["是", "否"])
            w.setCurrentIndex(0 if default else 1)
            return w
        if var_type == "Date":
            w = QDateEdit()
            w.setCalendarPopup(True)
            w.setDisplayFormat("yyyy-MM-dd")
            w.setDate(QDate.fromString(str(default), "yyyy-MM-dd"))
            return w
        if var_type == "Time":
            w = QTimeEdit()
            w.setDisplayFormat("HH:mm")
            w.setTime(QTime.fromString(str(default), "HH:mm"))
            return w
        if var_type == "Int":
            w = QSpinBox()
            w.setMinimum(-999999)
            w.setMaximum(999999)
            w.setValue(int(default) if default else 0)
            return w
        if var_type == "Float":
            w = QDoubleSpinBox()
            w.setMinimum(-999999.0)
            w.setMaximum(999999.0)
            w.setDecimals(2)
            w.setValue(float(default) if default else 0.0)
            return w
        w = QLineEdit()
        w.setText(str(default))
        return w

    def getMockData(
        self
    ) -> dict:

        data = {}
        for name, var_type, key_path, display_name in createTargetVarDefs():
            widget, _, _ = self._mockWidgets[name]
            value = self.getMockValue(widget, var_type)
            d = data
            for key in key_path[:-1]:
                d = d.setdefault(key, {})
            d[key_path[-1]] = value
        return data

    def setMockData(
        self,
        data: dict
    ):

        if not data:
            return
        for name, var_type, key_path, display_name in createTargetVarDefs():
            d = data
            try:
                for key in key_path:
                    d = d[key]
            except (KeyError, TypeError):
                continue
            widget, _, _ = self._mockWidgets[name]
            self.setMockValue(widget, var_type, d)

    def getMockValue(
        self,
        widget: QWidget,
        var_type: str
    ):

        if var_type == "Boolean":
            return widget.currentIndex() == 0
        if var_type == "Date":
            return widget.date().toString("yyyy-MM-dd")
        if var_type == "Time":
            return widget.time().toString("HH:mm")
        if var_type == "Int":
            return widget.value()
        if var_type == "Float":
            return widget.value()
        return widget.text()

    def setMockValue(
        self,
        widget: QWidget,
        var_type: str,
        value
    ):

        if var_type == "Boolean":
            widget.setCurrentIndex(0 if value else 1)
        elif var_type == "Date":
            widget.setDate(QDate.fromString(str(value), "yyyy-MM-dd"))
        elif var_type == "Time":
            widget.setTime(QTime.fromString(str(value), "HH:mm"))
        elif var_type == "Int":
            widget.setValue(int(value))
        elif var_type == "Float":
            widget.setValue(float(value))
        else:
            widget.setText(str(value))

    def connectSignals(
        self
    ):

        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)
        self.orchBtn.clicked.connect(self.onOpenOrchDialog)
        self.debugBtn.clicked.connect(self.onDebugRun)
        self.zoomInBtn.clicked.connect(self.onZoomIn)
        self.zoomOutBtn.clicked.connect(self.onZoomOut)
        self.zoomResetBtn.clicked.connect(self.onZoomReset)
        self.copyBtn.clicked.connect(self.onCopy)

    def getScript(
        self
    ) -> str:

        return self.textEdit.toPlainText()

    def updateFontSize(
        self
    ):

        self.textEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
            f"  font-size: {self._fontSize}px;"
            "}"
        )
        self.zoomLabel.setText(f"{self._fontSize}px")

    @Slot()
    def insertTemplate(
        self
    ):

        btn = self.sender()
        if not isinstance(btn, QPushButton):
            return
        template = btn.property("template")
        if not template:
            return
        cursor = self.textEdit.textCursor()
        cursor.insertText(template)

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

        self._fontSize = 21
        self.updateFontSize()

    @Slot()
    def onCopy(
        self
    ):

        clipboard = QApplication.clipboard()
        clipboard.setText(self.textEdit.toPlainText())
        self.copyBtn.setEnabled(False)
        QTimer.singleShot(2000, lambda: (
            self.copyBtn.setEnabled(True)
        ))

    @Slot()
    def onOpenOrchDialog(
        self
    ):

        from gui.ALAutoScriptOrchDialog import ALAutoScriptOrchDialog
        dlg = ALAutoScriptOrchDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            script = dlg.getScript()
            if script:
                cursor = self.textEdit.textCursor()
                cursor.insertText(script)
        dlg.deleteLater()

    @Slot()
    def onDebugRun(
        self
    ):

        script = self.textEdit.toPlainText().strip()
        if not script:
            QMessageBox.warning(self, "提示", "脚本内容为空。")
            return
        target_data = self.getMockData()
        before = deepcopy(target_data)
        try:
            engine = createEngine()
            engine.execute(script, target_data)
        except ValueError as e:
            QMessageBox.warning(self, "运行错误", str(e))
            return
        changes = []
        for name, var_type, key_path, display_name in createTargetVarDefs():
            before_val = before
            after_val = target_data
            try:
                for key in key_path:
                    before_val = before_val[key]
                    after_val = after_val[key]
            except (KeyError, TypeError):
                continue
            if before_val != after_val:
                changes.append((display_name, name, var_type, before_val, after_val))
        if not changes:
            QMessageBox.information(self, "调试运行", "目标变量未发生变化。")
            return
        dlg = _DebugResultDialog(changes, self)
        dlg.exec()
        dlg.deleteLater()
