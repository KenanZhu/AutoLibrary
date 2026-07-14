# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
"""
    Widget components for the AutoScript orchestration dialog.
"""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QStackedWidget
)

from gui.ALAutoScriptOrchDialog._helpers import (
    ACTION_OPTIONS,
    COMPARE_OPTIONS,
    LOGIC_OPTIONS,
    encodeValueStr,
    getPresetVars,
    getTypeOrder,
    getValueFromWidget,
    getArithType,
    makeComboWidget,
    makeLabel,
    makeOffsetWidget,
    makeValueWidget,
    makeVarRefCombo,
)


class ConditionRowFrame(QFrame):

    def __init__(
        self,
        var_mgr,
        parent_block_index: int = 0,
        is_first: bool = False,
        parent = None
    ):

        super().__init__(parent)
        self._var_mgr = var_mgr
        self._block_index = parent_block_index
        self._is_first = is_first
        self._is_bool_mode = False
        self._raw_rhs_expr = ""

        self.setupUi()
        self.connectSignals()

    def setupUi(
        self
    ):

        self.setUpdatesEnabled(False)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setFixedHeight(32)
        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(2, 2, 2, 2)
        Layout.setSpacing(4)
        if self._is_first:
            self.LogicCombo = None
        else:
            self.LogicCombo = makeComboWidget(LOGIC_OPTIONS, min_width=110, parent=self)
            Layout.addWidget(self.LogicCombo)
        self.LeftVarCombo = QComboBox(self)
        self.LeftVarCombo.setFixedHeight(25)
        self.LeftVarCombo.setMinimumWidth(120)
        self.LeftVarCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.populateLeftVarCombo()
        Layout.addWidget(self.LeftVarCombo)
        self.OpCombo = makeComboWidget(COMPARE_OPTIONS, min_width=80, parent=self)
        Layout.addWidget(self.OpCombo)
        self.CompTypeCombo = makeComboWidget([
            ("特定值", "literal"),
            ("变量", "variable"),
        ], min_width=70, parent=self)
        Layout.addWidget(self.CompTypeCombo)
        self.RhsStack = QStackedWidget(self)
        self.RhsStack.setFixedHeight(25)
        self.initLiteralStack()
        self.RhsVarCombo = makeVarRefCombo(self)
        self.RhsStack.addWidget(self.RhsVarCombo)
        self.RhsStack.setCurrentIndex(0)
        Layout.addWidget(self.RhsStack)
        if not self._is_first:
            self.DeleteBtn = QPushButton("×", self)
            self.DeleteBtn.setFixedSize(25, 25)
            self.DeleteBtn.setStyleSheet("color: red; font-weight: bold;")
            Layout.addWidget(self.DeleteBtn)
        else:
            self.DeleteBtn = None
        Layout.addStretch()
        self.setUpdatesEnabled(True)

    def populateLeftVarCombo(
        self
    ):

        was_bool = self._is_bool_mode
        bool_name = None
        if was_bool:
            data = self.LeftVarCombo.currentData()
            if data:
                bool_name = data[0]
        self._var_mgr.populateCombo(self.LeftVarCombo)
        # Append boolean literal sentinels at the end
        self.LeftVarCombo.insertSeparator(self.LeftVarCombo.count())
        self.LeftVarCombo.addItem("true", ("true", "Boolean"))
        self.LeftVarCombo.addItem("false", ("false", "Boolean"))
        if was_bool and bool_name:
            for ci in range(self.LeftVarCombo.count()):
                d = self.LeftVarCombo.itemData(ci)
                if d and d[0] == bool_name:
                    self.LeftVarCombo.setCurrentIndex(ci)
                    break

    def populateRHSVarCombo(
        self
    ):

        self._var_mgr.populateCombo(self.RhsVarCombo)

    def initLiteralStack(
        self
    ):

        self.LiteralStack = QStackedWidget(self)
        self.LiteralStack.setFixedHeight(25)
        self.literal_widgets = {}
        for vt in getTypeOrder():
            W = makeValueWidget(vt, self.LiteralStack)
            self.literal_widgets[vt] = W
            self.LiteralStack.addWidget(W)
        self.LiteralStack.setCurrentWidget(self.literal_widgets.get("String"))
        self.RhsStack.addWidget(self.LiteralStack)

    def connectSignals(
        self
    ):

        self.LeftVarCombo.currentIndexChanged.connect(self.onLeftVarChanged)
        self.CompTypeCombo.currentIndexChanged.connect(self.onCompTypeChanged)

    def getLogic(
        self
    ) -> str:

        return self.LogicCombo.currentData() if self.LogicCombo else ""

    def updateRHSLiteralWidget(
        self,
        vartype: str
    ):

        if vartype not in self.literal_widgets:
            vartype = "String"
        self.LiteralStack.setCurrentWidget(self.literal_widgets[vartype])

    def toScript(
        self
    ) -> str:

        data = self.LeftVarCombo.currentData()
        if self._is_bool_mode and data:
            return data[0]
        if not data:
            return ""
        name, vartype = data
        # CURRENT_DATE / CURRENT_TIME map to datenow() / timenow()
        if name == "CURRENT_DATE":
            name = "datenow()"
        elif name == "CURRENT_TIME":
            name = "timenow()"
        op_sym = self.OpCombo.currentData()
        if self._raw_rhs_expr:
            return f"{name} {op_sym} {self._raw_rhs_expr}"
        is_var_ref = (self.CompTypeCombo.currentData() == "variable")
        if is_var_ref:
            rd = self.RhsVarCombo.currentData()
            if rd:
                rhs_name = rd[0]
                if rhs_name == "CURRENT_DATE":
                    rhs_name = "datenow()"
                elif rhs_name == "CURRENT_TIME":
                    rhs_name = "timenow()"
                return f"{name} {op_sym} {rhs_name}"
            rhs_text = self.RhsVarCombo.currentText().strip()
            if rhs_text:
                return f"{name} {op_sym} {rhs_text}"
            return ""
        w = self.literal_widgets.get(vartype)
        if w:
            raw_val = getValueFromWidget(w)
            encoded = encodeValueStr(raw_val, vartype)
            return f"{name} {op_sym} {encoded}"
        return ""

    def refreshVarCombos(
        self
    ):

        self.populateLeftVarCombo()
        self.populateRHSVarCombo()

    @Slot(int)
    def onLeftVarChanged(
        self,
        idx
    ):

        self._raw_rhs_expr = ""
        if idx < 0:
            return
        data = self.LeftVarCombo.itemData(idx)
        if not data:
            return
        name, vartype = data
        is_bool = name in ("true", "false")
        self._is_bool_mode = is_bool
        self.OpCombo.setVisible(not is_bool)
        self.CompTypeCombo.setVisible(not is_bool)
        self.RhsStack.setVisible(not is_bool)
        if not is_bool:
            self.updateRHSLiteralWidget(vartype)

    @Slot(int)
    def onCompTypeChanged(
        self,
        idx
    ):

        self._raw_rhs_expr = ""
        isVar = (self.CompTypeCombo.currentData() == "variable")
        self.RhsStack.setCurrentIndex(1 if isVar else 0)
        if isVar:
            self.populateRHSVarCombo()


class ActionStepFrame(QFrame):

    def __init__(
        self,
        var_mgr,
        parent_block_index: int = 0,
        parent = None
    ):

        super().__init__(parent)
        self._var_mgr = var_mgr
        self._block_index = parent_block_index
        self._current_target_type = "String"

        self.setupUi()
        self.connectSignals()

    def setupUi(
        self
    ):

        self.setUpdatesEnabled(False)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setFixedHeight(35)
        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(2, 2, 2, 2)
        Layout.setSpacing(4)
        self.OpTypeCombo = makeComboWidget(ACTION_OPTIONS, min_width=70, parent=self)
        Layout.addWidget(self.OpTypeCombo)
        Layout.addWidget(makeLabel("设置", self))
        self.TargetCombo = QComboBox(self)
        self.TargetCombo.setFixedHeight(25)
        self.TargetCombo.setMinimumWidth(120)
        self.populateTargetCombo()
        Layout.addWidget(self.TargetCombo)
        Layout.addWidget(makeLabel("为", self))
        self.ValueSrcCombo = makeComboWidget([
            ("特定值", "literal"),
            ("变量", "variable"),
        ], min_width=70, parent=self)
        Layout.addWidget(self.ValueSrcCombo)
        self.ValueStack = QStackedWidget(self)
        self.ValueStack.setFixedHeight(25)
        self.initValueStacks()
        Layout.addWidget(self.ValueStack)
        self.ExistingVarCombo = makeVarRefCombo(self)
        self.ExistingVarCombo.setVisible(False)
        Layout.addWidget(self.ExistingVarCombo)
        self.DeleteBtn = QPushButton("×", self)
        self.DeleteBtn.setFixedSize(25, 25)
        self.DeleteBtn.setStyleSheet("color: red; font-weight: bold;")
        Layout.addWidget(self.DeleteBtn)
        self.setUpdatesEnabled(True)

    def populateTargetCombo(
        self
    ):

        self.TargetCombo.blockSignals(True)
        self.TargetCombo.clear()
        for p in getPresetVars():
            if p["name"] in ("CURRENT_TIME", "CURRENT_DATE"):
                continue
            info = self._var_mgr.getInfoByName(p["name"])
            if info:
                self.TargetCombo.addItem(
                    info["display"],
                    (info["name"], info["type"])
                )
        self.TargetCombo.blockSignals(False)

    def initValueStacks(
        self
    ):

        self.literal_widgets = {}
        self.offset_widgets = {}
        for vt in getTypeOrder():
            self.literal_widgets[vt] = makeValueWidget(vt, self.ValueStack)
            self.ValueStack.addWidget(self.literal_widgets[vt])
            if getArithType(vt):
                self.offset_widgets[vt] = makeOffsetWidget(vt, self.ValueStack)
                self.ValueStack.addWidget(self.offset_widgets[vt])
            else:
                Lbl = QLabel("(不支持该操作)", self.ValueStack)
                Lbl.setFixedHeight(25)
                self.offset_widgets[vt] = Lbl
                self.ValueStack.addWidget(Lbl)

    def connectSignals(
        self
    ):

        self.OpTypeCombo.currentIndexChanged.connect(self.onOpTypeChanged)
        self.TargetCombo.currentIndexChanged.connect(self.onTargetChanged)
        self.ValueSrcCombo.currentIndexChanged.connect(self.onValueSrcChanged)

    def getTargetName(
        self
    ) -> str:

        data = self.TargetCombo.currentData()
        return data[0] if data else ""

    def updateValueWidget(
        self
    ):

        op = self.OpTypeCombo.currentData()
        is_arith = (op in ("add", "sub"))
        actual_type = self._current_target_type
        if is_arith and actual_type in self.offset_widgets:
            self.ValueStack.setCurrentWidget(self.offset_widgets[actual_type])
        elif actual_type in self.literal_widgets:
            self.ValueStack.setCurrentWidget(self.literal_widgets[actual_type])
        else:
            self.ValueStack.setCurrentWidget(self.literal_widgets.get("String"))

    def toScript(
        self
    ) -> str:
        """
            Generate a single line of Lua script from the current widget state.
        """

        target = self.getTargetName()
        op = self.OpTypeCombo.currentData()
        if op == "pass":
            return "    -- pass"
        if not target:
            return ""
        raw_val = self.getValueRaw()
        vartype = self._current_target_type
        if op == "set":
            encoded = encodeValueStr(raw_val, vartype)
            return f"    {target} = {encoded}"
        elif op == "add":
            if vartype == "Date" and hasattr(self.ValueStack.currentWidget(), "getOffsetDays"):
                days = self.ValueStack.currentWidget().getOffsetDays()
                return f"    {target} = dateadd({target}, {days})"
            if vartype == "Time" and hasattr(self.ValueStack.currentWidget(), "getOffsetHours"):
                hours = self.ValueStack.currentWidget().getOffsetHours()
                return f"    {target} = timeadd({target}, {hours})"
            return f"    {target} = {target} + {raw_val}"
        elif op == "sub":
            if vartype == "Date" and hasattr(self.ValueStack.currentWidget(), "getOffsetDays"):
                days = self.ValueStack.currentWidget().getOffsetDays()
                return f"    {target} = dateadd({target}, -{days})"
            if vartype == "Time" and hasattr(self.ValueStack.currentWidget(), "getOffsetHours"):
                hours = self.ValueStack.currentWidget().getOffsetHours()
                return f"    {target} = timeadd({target}, -{hours})"
            return f"    {target} = {target} - {raw_val}"
        return ""

    def getValueRaw(
        self
    ) -> str:

        if self.ValueSrcCombo.currentData() == "variable":
            data = self.ExistingVarCombo.currentData()
            return data[0] if data else ""
        w = self.ValueStack.currentWidget()
        if w:
            return getValueFromWidget(w)
        return ""

    def refreshVarCombos(
        self
    ):

        current_data = self.TargetCombo.currentData()
        self.populateTargetCombo()
        if current_data:
            for i in range(self.TargetCombo.count()):
                d = self.TargetCombo.itemData(i)
                if d and d[0] == current_data[0]:
                    self.TargetCombo.setCurrentIndex(i)
                    break
        self._var_mgr.populateCombo(self.ExistingVarCombo)

    @Slot(int)
    def onTargetChanged(
        self,
        idx
    ):

        if idx < 0:
            return
        data = self.TargetCombo.itemData(idx)
        if not data:
            return
        _, vartype = data
        self._current_target_type = vartype
        self.updateValueWidget()
        self.onValueSrcChanged(self.ValueSrcCombo.currentIndex())

    @Slot(int)
    def onOpTypeChanged(
        self,
        idx
    ):

        self.updateValueWidget()

    @Slot(int)
    def onValueSrcChanged(
        self,
        idx
    ):

        is_var = (self.ValueSrcCombo.currentData() == "variable")
        self.ValueStack.setVisible(not is_var)
        self.ExistingVarCombo.setVisible(is_var)
        if is_var:
            self._var_mgr.populateCombo(self.ExistingVarCombo)
        else:
            self.updateValueWidget()
