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
        varMgr,
        parentBlockIndex: int = 0,
        isFirst: bool = False,
        parent = None
    ):

        super().__init__(parent)
        self._varMgr = varMgr
        self._blockIndex = parentBlockIndex
        self._isFirst = isFirst
        self._isBoolMode = False
        self._rawRhsExpr = ""

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
        if self._isFirst:
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
        self._CompTypeCombo = makeComboWidget([
            ("特定值", "literal"),
            ("变量", "variable"),
        ], min_width=70, parent=self)
        Layout.addWidget(self._CompTypeCombo)
        self.RhsStack = QStackedWidget(self)
        self.RhsStack.setFixedHeight(25)
        self.initLiteralStack()
        self.RhsVarCombo = makeVarRefCombo(self)
        self.RhsStack.addWidget(self.RhsVarCombo)
        self.RhsStack.setCurrentIndex(0)
        Layout.addWidget(self.RhsStack)
        if not self._isFirst:
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

        wasBool = self._isBoolMode
        boolName = None
        if wasBool:
            data = self.LeftVarCombo.currentData()
            if data:
                boolName = data[0]
        self._varMgr.populateCombo(self.LeftVarCombo)
        # Append boolean literal sentinels at the end
        self.LeftVarCombo.insertSeparator(self.LeftVarCombo.count())
        self.LeftVarCombo.addItem("true", ("true", "Boolean"))
        self.LeftVarCombo.addItem("false", ("false", "Boolean"))
        if wasBool and boolName:
            for ci in range(self.LeftVarCombo.count()):
                d = self.LeftVarCombo.itemData(ci)
                if d and d[0] == boolName:
                    self.LeftVarCombo.setCurrentIndex(ci)
                    break

    def populateRHSVarCombo(
        self
    ):

        self._varMgr.populateCombo(self.RhsVarCombo)

    def initLiteralStack(
        self
    ):

        self.LiteralStack = QStackedWidget(self)
        self.LiteralStack.setFixedHeight(25)
        self._literalWidgets = {}
        for vt in getTypeOrder():
            W = makeValueWidget(vt, self.LiteralStack)
            self._literalWidgets[vt] = W
            self.LiteralStack.addWidget(W)
        self.LiteralStack.setCurrentWidget(self._literalWidgets.get("String"))
        self.RhsStack.addWidget(self.LiteralStack)

    def connectSignals(
        self
    ):

        self.LeftVarCombo.currentIndexChanged.connect(self.onLeftVarChanged)
        self._CompTypeCombo.currentIndexChanged.connect(self.onCompTypeChanged)

    def getLogic(
        self
    ) -> str:

        return self.LogicCombo.currentData() if self.LogicCombo else ""

    def updateRHSLiteralWidget(
        self,
        vartype: str
    ):

        if vartype not in self._literalWidgets:
            vartype = "String"
        self.LiteralStack.setCurrentWidget(self._literalWidgets[vartype])

    def toScript(
        self
    ) -> str:

        data = self.LeftVarCombo.currentData()
        if self._isBoolMode and data:
            return data[0]
        if not data:
            return ""
        name, vartype = data
        # CURRENT_DATE / CURRENT_TIME map to datenow() / timenow()
        if name == "CURRENT_DATE":
            name = "datenow()"
        elif name == "CURRENT_TIME":
            name = "timenow()"
        opSym = self.OpCombo.currentData()
        if self._rawRhsExpr:
            return f"{name} {opSym} {self._rawRhsExpr}"
        isVarRef = (self._CompTypeCombo.currentData() == "variable")
        if isVarRef:
            rd = self.RhsVarCombo.currentData()
            if rd:
                rhsName = rd[0]
                if rhsName == "CURRENT_DATE":
                    rhsName = "datenow()"
                elif rhsName == "CURRENT_TIME":
                    rhsName = "timenow()"
                return f"{name} {opSym} {rhsName}"
            rhsText = self.RhsVarCombo.currentText().strip()
            if rhsText:
                return f"{name} {opSym} {rhsText}"
            return ""
        w = self._literalWidgets.get(vartype)
        if w:
            rawVal = getValueFromWidget(w)
            encoded = encodeValueStr(rawVal, vartype)
            return f"{name} {opSym} {encoded}"
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

        self._rawRhsExpr = ""
        if idx < 0:
            return
        data = self.LeftVarCombo.itemData(idx)
        if not data:
            return
        name, vartype = data
        isBool = name in ("true", "false")
        self._isBoolMode = isBool
        self.OpCombo.setVisible(not isBool)
        self._CompTypeCombo.setVisible(not isBool)
        self.RhsStack.setVisible(not isBool)
        if not isBool:
            self.updateRHSLiteralWidget(vartype)

    @Slot(int)
    def onCompTypeChanged(
        self,
        idx
    ):

        self._rawRhsExpr = ""
        isVar = (self._CompTypeCombo.currentData() == "variable")
        self.RhsStack.setCurrentIndex(1 if isVar else 0)
        if isVar:
            self.populateRHSVarCombo()


class ActionStepFrame(QFrame):

    def __init__(
        self,
        varMgr,
        parentBlockIndex: int = 0,
        parent = None
    ):

        super().__init__(parent)
        self._varMgr = varMgr
        self._blockIndex = parentBlockIndex
        self._currentTargetType = "String"

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
            info = self._varMgr.getInfoByName(p["name"])
            if info:
                self.TargetCombo.addItem(
                    info["display"],
                    (info["name"], info["type"])
                )
        self.TargetCombo.blockSignals(False)

    def initValueStacks(
        self
    ):

        self._literalWidgets = {}
        self._offsetWidgets = {}
        for vt in getTypeOrder():
            self._literalWidgets[vt] = makeValueWidget(vt, self.ValueStack)
            self.ValueStack.addWidget(self._literalWidgets[vt])
            if getArithType(vt):
                self._offsetWidgets[vt] = makeOffsetWidget(vt, self.ValueStack)
                self.ValueStack.addWidget(self._offsetWidgets[vt])
            else:
                Lbl = QLabel("(不支持该操作)", self.ValueStack)
                Lbl.setFixedHeight(25)
                self._offsetWidgets[vt] = Lbl
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
        isArith = (op in ("add", "sub"))
        actualType = self._currentTargetType
        if isArith and actualType in self._offsetWidgets:
            self.ValueStack.setCurrentWidget(self._offsetWidgets[actualType])
        elif actualType in self._literalWidgets:
            self.ValueStack.setCurrentWidget(self._literalWidgets[actualType])
        else:
            self.ValueStack.setCurrentWidget(self._literalWidgets.get("String"))

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
        rawVal = self.getValueRaw()
        vartype = self._currentTargetType
        if op == "set":
            encoded = encodeValueStr(rawVal, vartype)
            return f"    {target} = {encoded}"
        elif op == "add":
            if vartype == "Date" and hasattr(self.ValueStack.currentWidget(), "getOffsetDays"):
                days = self.ValueStack.currentWidget().getOffsetDays()
                return f"    {target} = dateadd({target}, {days})"
            if vartype == "Time" and hasattr(self.ValueStack.currentWidget(), "getOffsetHours"):
                hours = self.ValueStack.currentWidget().getOffsetHours()
                return f"    {target} = timeadd({target}, {hours})"
            return f"    {target} = {target} + {rawVal}"
        elif op == "sub":
            if vartype == "Date" and hasattr(self.ValueStack.currentWidget(), "getOffsetDays"):
                days = self.ValueStack.currentWidget().getOffsetDays()
                return f"    {target} = dateadd({target}, -{days})"
            if vartype == "Time" and hasattr(self.ValueStack.currentWidget(), "getOffsetHours"):
                hours = self.ValueStack.currentWidget().getOffsetHours()
                return f"    {target} = timeadd({target}, -{hours})"
            return f"    {target} = {target} - {rawVal}"
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

        currentData = self.TargetCombo.currentData()
        self.populateTargetCombo()
        if currentData:
            for i in range(self.TargetCombo.count()):
                d = self.TargetCombo.itemData(i)
                if d and d[0] == currentData[0]:
                    self.TargetCombo.setCurrentIndex(i)
                    break
        self._varMgr.populateCombo(self.ExistingVarCombo)

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
        self._currentTargetType = vartype
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

        isVar = (self.ValueSrcCombo.currentData() == "variable")
        self.ValueStack.setVisible(not isVar)
        self.ExistingVarCombo.setVisible(isVar)
        if isVar:
            self._varMgr.populateCombo(self.ExistingVarCombo)
        else:
            self.updateValueWidget()
