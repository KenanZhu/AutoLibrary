# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from copy import deepcopy

import qtawesome as qta

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

        KeywordFmt = QTextCharFormat()
        KeywordFmt.setForeground(QColor("#569CD6"))
        KeywordFmt.setFontWeight(QFont.Weight.Bold)
        for kw in [
            "if", "elseif", "else", "end", "then",
            "and", "or", "not",
            "local", "function", "return", "nil",
        ]:
            self._rules.append((r"\b" + kw + r"\b", KeywordFmt))
        BoolFmt = QTextCharFormat()
        BoolFmt.setForeground(QColor("#4FC1FF"))
        BoolFmt.setFontWeight(QFont.Weight.Bold)
        self._rules.append((r"\btrue\b", BoolFmt))
        self._rules.append((r"\bfalse\b", BoolFmt))
        CmpFmt = QTextCharFormat()
        CmpFmt.setForeground(QColor("#C586C0"))
        CmpFmt.setFontWeight(QFont.Weight.Normal)
        for op in [r"==", r"~=", r">=", r"<=", r">", r"<"]:
            self._rules.append((op, CmpFmt))
        ArithFmt = QTextCharFormat()
        ArithFmt.setForeground(QColor("#C586C0"))
        ArithFmt.setFontWeight(QFont.Weight.Normal)
        for op in [r"\+", r"-", r"\*", r"/", r"\.\."]:
            self._rules.append((op, ArithFmt))
        FuncFmt = QTextCharFormat()
        FuncFmt.setForeground(QColor("#DCDCAA"))
        FuncFmt.setFontWeight(QFont.Weight.Normal)
        for fn in [ "time", "date", "datenow", "timenow", "dateadd", "timeadd"]:
            self._rules.append((r"\b" + fn + r"\b", FuncFmt))
        VarFmt = QTextCharFormat()
        VarFmt.setForeground(QColor("#9CDCFE"))
        VarFmt.setFontWeight(QFont.Weight.Normal)
        var_names = [name for _, (name, _) in createAllVariablesTable().items()]
        for var in var_names:
            self._rules.append((r"\b" + var + r"\b", VarFmt))
        StrFmt = QTextCharFormat()
        StrFmt.setForeground(QColor("#CE9178"))
        StrFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r'"[^"]*"', StrFmt))
        self._rules.append((r"'[^']*'", StrFmt))
        NumFmt = QTextCharFormat()
        NumFmt.setForeground(QColor("#B5CEA8"))
        NumFmt.setFontWeight(QFont.Weight.Normal)
        self._rules.append((r"\b\d+(?:\.\d+)?\b", NumFmt))
        CommentFmt = QTextCharFormat()
        CommentFmt.setForeground(QColor("#6A9955"))
        CommentFmt.setFontItalic(True)
        self._rules.append((r"--[^\n]*", CommentFmt))

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
        DbgLayout = QVBoxLayout(self)
        DbgTable = QTableWidget(len(changes), 3)
        DbgTable.setHorizontalHeaderLabels(["目标变量", "原始数据", "运行后数据"])
        DbgTable.horizontalHeader().setStretchLastSection(True)
        DbgTable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        DbgTable.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (display_name, name, var_type, before_val, after_val) in enumerate(changes):
            label = f"{display_name}: {name}({var_type})"
            DbgTable.setItem(row, 0, QTableWidgetItem(label))
            DbgTable.setItem(row, 1, QTableWidgetItem(str(before_val)))
            DbgTable.setItem(row, 2, QTableWidgetItem(str(after_val)))
        DbgLayout.addWidget(DbgTable)
        DbgBtnBox = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        DbgBtnBox.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        DbgBtnBox.accepted.connect(self.accept)
        DbgLayout.addWidget(DbgBtnBox)


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
        self.TextEdit.setPlainText(script)
        self._Highlighter = ALScriptHighlighter(
            self.TextEdit.document()
        )
        if mockData:
            self.setMockData(mockData)

    def setupUi(
        self
    ):

        self.setWindowTitle("AutoScript 编辑 - AutoLibrary")
        self.setMinimumSize(660, 600)
        Layout = QVBoxLayout(self)
        Layout.setSpacing(3)
        Layout.setContentsMargins(3, 3, 3, 3)
        ToolbarLayout = QHBoxLayout()
        self.ZoomInBtn = QPushButton("")
        self.ZoomInBtn.setIcon(qta.icon("fa6s.plus", color=self._iconColor()))
        self.ZoomInBtn.setIconSize(QSize(14, 14))
        self.ZoomInBtn.setFixedSize(25, 25)
        self.ZoomOutBtn = QPushButton("")
        self.ZoomOutBtn.setIcon(qta.icon("fa6s.minus", color=self._iconColor()))
        self.ZoomOutBtn.setIconSize(QSize(14, 14))
        self.ZoomOutBtn.setFixedSize(25, 25)
        self.ZoomResetBtn = QPushButton("")
        self.ZoomResetBtn.setIcon(qta.icon("fa6s.rotate-left", color=self._iconColor()))
        self.ZoomResetBtn.setIconSize(QSize(14, 14))
        self.ZoomResetBtn.setFixedSize(25, 25)
        self.ZoomResetBtn.setToolTip("重置缩放")
        self.ZoomLabel = QLabel(f"{self._fontSize}px")
        self.ZoomLabel.setFixedHeight(25)
        self.OrchBtn = QPushButton("编排")
        self.OrchBtn.setFixedSize(80, 25)
        self.OrchBtn.setToolTip("可视化生成 AutoScript 代码并插入到光标位置")
        ToolbarLayout.addWidget(self.OrchBtn)
        self.DebugBtn = QPushButton("▶ 调试运行")
        self.DebugBtn.setFixedSize(80, 25)
        self.DebugBtn.setToolTip("使用右侧模拟数据执行脚本，查看目标变量变化")
        ToolbarLayout.addWidget(self.DebugBtn)
        Sep = QFrame()
        Sep.setFrameShape(QFrame.Shape.VLine)
        Sep.setFrameShadow(QFrame.Shadow.Sunken)
        Sep.setFixedWidth(1)
        ToolbarLayout.addWidget(Sep)
        ToolbarLayout.addWidget(self.ZoomInBtn)
        ToolbarLayout.addWidget(self.ZoomOutBtn)
        ToolbarLayout.addWidget(self.ZoomResetBtn)
        ToolbarLayout.addWidget(self.ZoomLabel)
        ToolbarLayout.addStretch()
        self.CopyBtn = QPushButton("")
        self.CopyBtn.setIcon(qta.icon("fa6s.copy", color=self._iconColor()))
        self.CopyBtn.setIconSize(QSize(14, 14))
        self.CopyBtn.setFixedSize(25, 25)
        self.CopyBtn.setToolTip("复制脚本")
        ToolbarLayout.addWidget(self.CopyBtn)
        Layout.addLayout(ToolbarLayout)
        self.TextEdit = _TabToSpacesEditor(self)
        self.TextEdit.setTabStopDistance(40)
        self.TextEdit.setLineWrapMode(
            QPlainTextEdit.LineWrapMode.NoWrap
        )
        self.TextEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
           f"  font-size: {self._fontSize}px;"
            "}"
        )
        Layout.addWidget(self.TextEdit)
        self.createButtonPanel(Layout)
        self.BtnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.BtnBox.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        self.BtnBox.button(QDialogButtonBox.StandardButton.Ok).setFixedSize(80, 25)
        self.BtnBox.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        self.BtnBox.button(QDialogButtonBox.StandardButton.Cancel).setFixedSize(80, 25)
        Layout.addWidget(self.BtnBox)

    def createButtonPanel(
        self,
        ParentLayout
    ):

        Splitter = QSplitter(Qt.Orientation.Horizontal)
        TabWidget = QTabWidget()
        TabWidget.setMaximumHeight(150)
        BasicWidget = QWidget()
        BasicLayout = QGridLayout(BasicWidget)
        BasicLayout.setSpacing(4)
        BasicLayout.setContentsMargins(4, 4, 4, 4)
        BasicLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        controlButtons = [
            ("如果 (if...)", "if  then\n    \nend"),
            ("再如果 (elseif...)", "elseif  then\n    "),
            ("否则 (else)", "else"),
            ("结束 (end)", "end"),
            ("跳过 (pass)", "-- pass"),
        ]
        self.addButtonsToGrid(BasicLayout, controlButtons, 0, 0, 3)
        assignButtons = [
            ("赋值 (=)", " = "),
        ]
        self.addButtonsToGrid(BasicLayout, assignButtons, 1, 2, 3)
        TabWidget.addTab(BasicWidget, "基本语法")
        OperatorWidget = QWidget()
        OperatorLayout = QGridLayout(OperatorWidget)
        OperatorLayout.setSpacing(4)
        OperatorLayout.setContentsMargins(4, 4, 4, 4)
        OperatorLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        arithmeticButtons = [
            ("加 (+)", " + "),
            ("减 (-)", " - "),
        ]
        self.addButtonsToGrid(OperatorLayout, arithmeticButtons, 0, 0, 3)
        compareButtons = [
            ("等于 (==)", " == "),
            ("不等于 (~=)", " ~= "),
            ("大于 (>)", " > "),
            ("小于 (<)", " < "),
            ("大于等于 (>=)", " >= "),
            ("小于等于 (<=)", " <= "),
        ]
        self.addButtonsToGrid(OperatorLayout, compareButtons, 1, 0, 3)
        logic_buttons = [
            ("且 (and)", " and "),
            ("或 (or)", " or "),
        ]
        self.addButtonsToGrid(OperatorLayout, logic_buttons, 2, 0, 3)
        TabWidget.addTab(OperatorWidget, "运算符")
        LiteralWidget = QWidget()
        LiteralLayout = QGridLayout(LiteralWidget)
        LiteralLayout.setSpacing(4)
        LiteralLayout.setContentsMargins(4, 4, 4, 4)
        LiteralLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        bool_buttons = [
            ("真 (true)", "true"),
            ("假 (false)", "false"),
        ]
        self.addButtonsToGrid(LiteralLayout, bool_buttons, 0, 0, 3)
        dateTimeButtons = [
            ("日期", 'date(2026, 1, 1)'),
            ("时间", 'time(0, 0)'),
        ]
        self.addButtonsToGrid(LiteralLayout, dateTimeButtons, 1, 0, 3)
        hintButtons = [
            ("字符串", '"请输入文本"'),
            ("数字", "123"),
            ("注释", "-- 请输入注释"),
        ]
        self.addButtonsToGrid(LiteralLayout, hintButtons, 2, 0, 3)
        TabWidget.addTab(LiteralWidget, "字面量")
        VarWidget = QWidget()
        VarLayout = QGridLayout(VarWidget)
        VarLayout.setSpacing(4)
        VarLayout.setContentsMargins(4, 4, 4, 4)
        VarLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        varButtons = [
            (display_name, name) for display_name, (name, _) in createAllVariablesTable().items()
        ]
        self.addButtonsToGrid(VarLayout, varButtons, 0, 0, 3)
        TabWidget.addTab(VarWidget, "变量")
        FuncWidget = QWidget()
        FuncLayout = QGridLayout(FuncWidget)
        FuncLayout.setSpacing(4)
        FuncLayout.setContentsMargins(4, 4, 4, 4)
        FuncLayout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        funcButtons = [
            ("datenow()", "datenow()", "返回当前日期的 Unix 时间戳"),
            ("timenow()", "timenow()", "返回当前时间在一天中的分钟数"),
            ("dateadd(day, n)", "dateadd(, )", "日期偏移: dateadd(日期时间戳, 天数)"),
            ("timeadd(time, n)", "timeadd(, )", "时间偏移: timeadd(分钟数, 分钟数)"),
        ]
        for i, (text, template, tooltip) in enumerate(funcButtons):
            Btn = QPushButton(text)
            Btn.setProperty("template", template)
            Btn.clicked.connect(self.insertTemplate)
            Btn.setFixedWidth(100)
            Btn.setFixedHeight(25)
            Btn.setToolTip(tooltip)
            FuncLayout.addWidget(Btn, i // 2, i % 2)
        TabWidget.addTab(FuncWidget, "工具函数")
        MockPanel = self.createMockPanel()
        MockPanel.setMinimumWidth(260)
        Splitter.addWidget(TabWidget)
        Splitter.addWidget(MockPanel)
        Splitter.setStretchFactor(0, 1)
        Splitter.setStretchFactor(1, 1)
        Splitter.setSizes([530, 530])
        ParentLayout.addWidget(Splitter)

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
            Btn = QPushButton(btn_text)
            Btn.setProperty("template", template)
            Btn.clicked.connect(self.insertTemplate)
            Btn.setFixedWidth(100)
            Btn.setFixedHeight(25)
            Btn.setToolTip(f"插入: {template}")
            grid_layout.addWidget(Btn, row, col)
            col += 1
            if col >= start_col + max_columns:
                col = start_col
                row += 1

    def createMockPanel(
        self
    ) -> QGroupBox:

        Group = QGroupBox("模拟目标数据")
        Form = QFormLayout(Group)
        Form.setSpacing(4)
        Form.setContentsMargins(5, 10, 5, 5)
        self._mockWidgets = {}
        mockData = createMockTargetData()
        for name, var_type, key_path, display_name in createTargetVarDefs():
            d = mockData
            for key in key_path:
                d = d[key]
            default = d
            Widget = self.makeMockInput(var_type, default)
            Label = QLabel(f"{display_name}: {name}({var_type})")
            Form.addRow(Label, Widget)
            self._mockWidgets[name] = (Widget, var_type, key_path)
        return Group

    def makeMockInput(
        self,
        var_type: str,
        default
    ) -> QWidget:

        if var_type == "String":
            W = QLineEdit()
            W.setText(str(default))
            return W
        if var_type == "Boolean":
            W = QComboBox()
            W.addItems(["是", "否"])
            W.setCurrentIndex(0 if default else 1)
            return W
        if var_type == "Date":
            W = QDateEdit()
            W.setCalendarPopup(True)
            W.setDisplayFormat("yyyy-MM-dd")
            W.setDate(QDate.fromString(str(default), "yyyy-MM-dd"))
            return W
        if var_type == "Time":
            W = QTimeEdit()
            W.setDisplayFormat("HH:mm")
            W.setTime(QTime.fromString(str(default), "HH:mm"))
            return W
        if var_type == "Int":
            W = QSpinBox()
            W.setMinimum(-999999)
            W.setMaximum(999999)
            W.setValue(int(default) if default else 0)
            return W
        if var_type == "Float":
            W = QDoubleSpinBox()
            W.setMinimum(-999999.0)
            W.setMaximum(999999.0)
            W.setDecimals(2)
            W.setValue(float(default) if default else 0.0)
            return W
        W = QLineEdit()
        W.setText(str(default))
        return W

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

    def _iconColor(
        self
    ) -> str:

        return QApplication.instance().palette().color(
            QApplication.instance().palette().ColorRole.WindowText
        ).name()

    def connectSignals(
        self
    ):

        self.BtnBox.accepted.connect(self.accept)
        self.BtnBox.rejected.connect(self.reject)
        self.OrchBtn.clicked.connect(self.onOpenOrchDialog)
        self.DebugBtn.clicked.connect(self.onDebugRun)
        self.ZoomInBtn.clicked.connect(self.onZoomIn)
        self.ZoomOutBtn.clicked.connect(self.onZoomOut)
        self.ZoomResetBtn.clicked.connect(self.onZoomReset)
        self.CopyBtn.clicked.connect(self.onCopy)

    def getScript(
        self
    ) -> str:

        return self.TextEdit.toPlainText()

    def updateFontSize(
        self
    ):

        self.TextEdit.setStyleSheet(
            "QPlainTextEdit {"
            "  font-family: 'Courier New', 'Consolas', monospace;"
            f"  font-size: {self._fontSize}px;"
            "}"
        )
        self.ZoomLabel.setText(f"{self._fontSize}px")

    @Slot()
    def insertTemplate(
        self
    ):

        Btn = self.sender()
        if not isinstance(Btn, QPushButton):
            return
        template = Btn.property("template")
        if not template:
            return
        cursor = self.TextEdit.textCursor()
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

        Clipboard = QApplication.clipboard()
        Clipboard.setText(self.TextEdit.toPlainText())
        self.CopyBtn.setEnabled(False)
        QTimer.singleShot(2000, lambda: (
            self.CopyBtn.setEnabled(True)
        ))

    @Slot()
    def onOpenOrchDialog(
        self
    ):

        from gui.ALAutoScriptOrchDialog import ALAutoScriptOrchDialog
        Dlg = ALAutoScriptOrchDialog(self)
        if Dlg.exec() == QDialog.DialogCode.Accepted:
            script = Dlg.getScript()
            if script:
                cursor = self.TextEdit.textCursor()
                cursor.insertText(script)
        Dlg.deleteLater()

    @Slot()
    def onDebugRun(
        self
    ):

        script = self.TextEdit.toPlainText().strip()
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
        Dlg = _DebugResultDialog(changes, self)
        Dlg.exec()
        Dlg.deleteLater()
