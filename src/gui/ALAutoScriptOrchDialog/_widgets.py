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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        if self._isFirst:
            self.logicCombo = None
        else:
            self.logicCombo = makeComboWidget(LOGIC_OPTIONS, min_width=110, parent=self)
            layout.addWidget(self.logicCombo)
        self.leftVarCombo = QComboBox(self)
        self.leftVarCombo.setFixedHeight(25)
        self.leftVarCombo.setMinimumWidth(120)
        self.leftVarCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.populateLeftVarCombo()
        layout.addWidget(self.leftVarCombo)
        self.opCombo = makeComboWidget(COMPARE_OPTIONS, min_width=80, parent=self)
        layout.addWidget(self.opCombo)
        self._compTypeCombo = makeComboWidget([
            ("特定值", "literal"),
            ("变量", "variable"),
        ], min_width=70, parent=self)
        layout.addWidget(self._compTypeCombo)
        self.rhsStack = QStackedWidget(self)
        self.rhsStack.setFixedHeight(25)
        self.initLiteralStack()
        self.rhsVarCombo = makeVarRefCombo(self)
        self.rhsStack.addWidget(self.rhsVarCombo)
        self.rhsStack.setCurrentIndex(0)
        layout.addWidget(self.rhsStack)
        if not self._isFirst:
            self.deleteBtn = QPushButton("×", self)
            self.deleteBtn.setFixedSize(25, 25)
            self.deleteBtn.setStyleSheet("color: red; font-weight: bold;")
            layout.addWidget(self.deleteBtn)
        else:
            self.deleteBtn = None
        layout.addStretch()
        self.setUpdatesEnabled(True)

    def populateLeftVarCombo(
        self
    ):

        wasBool = self._isBoolMode
        boolName = None
        if wasBool:
            data = self.leftVarCombo.currentData()
            if data:
                boolName = data[0]
        self._varMgr.populateCombo(self.leftVarCombo)
        # Append boolean literal sentinels at the end
        self.leftVarCombo.insertSeparator(self.leftVarCombo.count())
        self.leftVarCombo.addItem("true", ("true", "Boolean"))
        self.leftVarCombo.addItem("false", ("false", "Boolean"))
        if wasBool and boolName:
            for ci in range(self.leftVarCombo.count()):
                d = self.leftVarCombo.itemData(ci)
                if d and d[0] == boolName:
                    self.leftVarCombo.setCurrentIndex(ci)
                    break

    def populateRHSVarCombo(
        self
    ):

        self._varMgr.populateCombo(self.rhsVarCombo)

    def initLiteralStack(
        self
    ):

        self.literalStack = QStackedWidget(self)
        self.literalStack.setFixedHeight(25)
        self._literalWidgets = {}
        for vt in getTypeOrder():
            w = makeValueWidget(vt, self.literalStack)
            self._literalWidgets[vt] = w
            self.literalStack.addWidget(w)
        self.literalStack.setCurrentWidget(self._literalWidgets.get("String"))
        self.rhsStack.addWidget(self.literalStack)

    def connectSignals(
        self
    ):

        self.leftVarCombo.currentIndexChanged.connect(self.onLeftVarChanged)
        self._compTypeCombo.currentIndexChanged.connect(self.onCompTypeChanged)

    def getLogic(
        self
    ) -> str:

        return self.logicCombo.currentData() if self.logicCombo else ""

    def updateRHSLiteralWidget(
        self,
        vartype: str
    ):

        if vartype not in self._literalWidgets:
            vartype = "String"
        self.literalStack.setCurrentWidget(self._literalWidgets[vartype])

    def toScript(
        self
    ) -> str:

        data = self.leftVarCombo.currentData()
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
        opSym = self.opCombo.currentData()
        if self._rawRhsExpr:
            return f"{name} {opSym} {self._rawRhsExpr}"
        isVarRef = (self._compTypeCombo.currentData() == "variable")
        if isVarRef:
            rd = self.rhsVarCombo.currentData()
            if rd:
                rhsName = rd[0]
                if rhsName == "CURRENT_DATE":
                    rhsName = "datenow()"
                elif rhsName == "CURRENT_TIME":
                    rhsName = "timenow()"
                return f"{name} {opSym} {rhsName}"
            rhsText = self.rhsVarCombo.currentText().strip()
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
        data = self.leftVarCombo.itemData(idx)
        if not data:
            return
        name, vartype = data
        isBool = name in ("true", "false")
        self._isBoolMode = isBool
        self.opCombo.setVisible(not isBool)
        self._compTypeCombo.setVisible(not isBool)
        self.rhsStack.setVisible(not isBool)
        if not isBool:
            self.updateRHSLiteralWidget(vartype)

    @Slot(int)
    def onCompTypeChanged(
        self,
        idx
    ):

        self._rawRhsExpr = ""
        isVar = (self._compTypeCombo.currentData() == "variable")
        self.rhsStack.setCurrentIndex(1 if isVar else 0)
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        self.opTypeCombo = makeComboWidget(ACTION_OPTIONS, min_width=70, parent=self)
        layout.addWidget(self.opTypeCombo)
        layout.addWidget(makeLabel("设置", self))
        self.targetCombo = QComboBox(self)
        self.targetCombo.setFixedHeight(25)
        self.targetCombo.setMinimumWidth(120)
        self.populateTargetCombo()
        layout.addWidget(self.targetCombo)
        layout.addWidget(makeLabel("为", self))
        self.valueSrcCombo = makeComboWidget([
            ("特定值", "literal"),
            ("变量", "variable"),
        ], min_width=70, parent=self)
        layout.addWidget(self.valueSrcCombo)
        self.valueStack = QStackedWidget(self)
        self.valueStack.setFixedHeight(25)
        self.initValueStacks()
        layout.addWidget(self.valueStack)
        self.existingVarCombo = makeVarRefCombo(self)
        self.existingVarCombo.setVisible(False)
        layout.addWidget(self.existingVarCombo)
        self.deleteBtn = QPushButton("×", self)
        self.deleteBtn.setFixedSize(25, 25)
        self.deleteBtn.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.deleteBtn)
        self.setUpdatesEnabled(True)

    def populateTargetCombo(
        self
    ):

        self.targetCombo.blockSignals(True)
        self.targetCombo.clear()
        for p in getPresetVars():
            if p["name"] in ("CURRENT_TIME", "CURRENT_DATE"):
                continue
            info = self._varMgr.getInfoByName(p["name"])
            if info:
                self.targetCombo.addItem(
                    info["display"],
                    (info["name"], info["type"])
                )
        self.targetCombo.blockSignals(False)

    def initValueStacks(
        self
    ):

        self._literalWidgets = {}
        self._offsetWidgets = {}
        for vt in getTypeOrder():
            self._literalWidgets[vt] = makeValueWidget(vt, self.valueStack)
            self.valueStack.addWidget(self._literalWidgets[vt])
            if getArithType(vt):
                self._offsetWidgets[vt] = makeOffsetWidget(vt, self.valueStack)
                self.valueStack.addWidget(self._offsetWidgets[vt])
            else:
                lbl = QLabel("(不支持该操作)", self.valueStack)
                lbl.setFixedHeight(25)
                self._offsetWidgets[vt] = lbl
                self.valueStack.addWidget(lbl)

    def connectSignals(
        self
    ):

        self.opTypeCombo.currentIndexChanged.connect(self.onOpTypeChanged)
        self.targetCombo.currentIndexChanged.connect(self.onTargetChanged)
        self.valueSrcCombo.currentIndexChanged.connect(self.onValueSrcChanged)

    def getTargetName(
        self
    ) -> str:

        data = self.targetCombo.currentData()
        return data[0] if data else ""

    def updateValueWidget(
        self
    ):

        op = self.opTypeCombo.currentData()
        isArith = (op in ("add", "sub"))
        actualType = self._currentTargetType
        if isArith and actualType in self._offsetWidgets:
            self.valueStack.setCurrentWidget(self._offsetWidgets[actualType])
        elif actualType in self._literalWidgets:
            self.valueStack.setCurrentWidget(self._literalWidgets[actualType])
        else:
            self.valueStack.setCurrentWidget(self._literalWidgets.get("String"))

    def toScript(
        self
    ) -> str:
        """
            Generate a single line of Lua script from the current widget state.
        """

        target = self.getTargetName()
        op = self.opTypeCombo.currentData()
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
            if vartype == "Date" and hasattr(self.valueStack.currentWidget(), "getOffsetDays"):
                days = self.valueStack.currentWidget().getOffsetDays()
                return f"    {target} = dateadd({target}, {days})"
            if vartype == "Time" and hasattr(self.valueStack.currentWidget(), "getOffsetHours"):
                hours = self.valueStack.currentWidget().getOffsetHours()
                return f"    {target} = timeadd({target}, {hours})"
            return f"    {target} = {target} + {rawVal}"
        elif op == "sub":
            if vartype == "Date" and hasattr(self.valueStack.currentWidget(), "getOffsetDays"):
                days = self.valueStack.currentWidget().getOffsetDays()
                return f"    {target} = dateadd({target}, -{days})"
            if vartype == "Time" and hasattr(self.valueStack.currentWidget(), "getOffsetHours"):
                hours = self.valueStack.currentWidget().getOffsetHours()
                return f"    {target} = timeadd({target}, -{hours})"
            return f"    {target} = {target} - {rawVal}"
        return ""

    def getValueRaw(
        self
    ) -> str:

        if self.valueSrcCombo.currentData() == "variable":
            data = self.existingVarCombo.currentData()
            return data[0] if data else ""
        w = self.valueStack.currentWidget()
        if w:
            return getValueFromWidget(w)
        return ""

    def refreshVarCombos(
        self
    ):

        currentData = self.targetCombo.currentData()
        self.populateTargetCombo()
        if currentData:
            for i in range(self.targetCombo.count()):
                d = self.targetCombo.itemData(i)
                if d and d[0] == currentData[0]:
                    self.targetCombo.setCurrentIndex(i)
                    break
        self._varMgr.populateCombo(self.existingVarCombo)

    @Slot(int)
    def onTargetChanged(
        self,
        idx
    ):

        if idx < 0:
            return
        data = self.targetCombo.itemData(idx)
        if not data:
            return
        _, vartype = data
        self._currentTargetType = vartype
        self.updateValueWidget()
        self.onValueSrcChanged(self.valueSrcCombo.currentIndex())

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

        isVar = (self.valueSrcCombo.currentData() == "variable")
        self.valueStack.setVisible(not isVar)
        self.existingVarCombo.setVisible(isVar)
        if isVar:
            self._varMgr.populateCombo(self.existingVarCombo)
        else:
            self.updateValueWidget()
