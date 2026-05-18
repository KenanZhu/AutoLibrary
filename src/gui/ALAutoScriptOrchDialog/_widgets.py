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
    ACTION_TYPES,
    ARITH_TYPES,
    COMPARE_OPERATORS,
    LOGIC_OPERATORS,
    PRESET_VARIABLES,
    VAR_TYPE_ORDER,
    encodeValueStr,
    getValueFromWidget,
    isVarReference,
    makeComboWidget,
    makeLabel,
    makeOffsetWidget,
    makeValueWidget,
    makeVarRefCombo,
    setWidgetValue,
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
            self.logicCombo = makeComboWidget(LOGIC_OPERATORS, min_width=110, parent=self)
            layout.addWidget(self.logicCombo)
        self.leftVarCombo = QComboBox(self)
        self.leftVarCombo.setFixedHeight(25)
        self.leftVarCombo.setMinimumWidth(120)
        self.leftVarCombo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.populateLeftVarCombo()
        layout.addWidget(self.leftVarCombo)
        self.opCombo = makeComboWidget(COMPARE_OPERATORS, min_width=80, parent=self)
        layout.addWidget(self.opCombo)
        self._compTypeCombo = makeComboWidget([
            ("特定值", "literal"),
            ("变量", "variable"),
        ], min_width=70, parent=self)
        layout.addWidget(self._compTypeCombo)
        self.rhsStack = QStackedWidget(self)
        self.rhsStack.setFixedHeight(25)
        self.literalStack = QStackedWidget(self)
        self.literalStack.setFixedHeight(25)
        self.literalWidgets = {}
        for vt in VAR_TYPE_ORDER:
            w = makeValueWidget(vt, self.literalStack)
            self.literalWidgets[vt] = w
            self.literalStack.addWidget(w)
        self.literalStack.setCurrentWidget(self.literalWidgets.get("String"))
        self.rhsStack.addWidget(self.literalStack)
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

        self._varMgr.populateCombo(self.leftVarCombo)


    def populateRhsVarCombo(
        self
    ):

        self._varMgr.populateCombo(self.rhsVarCombo)


    def connectSignals(
        self
    ):

        self.leftVarCombo.currentIndexChanged.connect(self.onLeftVarChanged)
        self._compTypeCombo.currentIndexChanged.connect(self.onCompTypeChanged)

    @Slot(int)
    def onLeftVarChanged(
        self,
        idx
    ):

        if idx < 0:
            return
        data = self.leftVarCombo.itemData(idx)
        if not data:
            return
        _, vartype = data
        self.updateRhsLiteralWidget(vartype)


    def updateRhsLiteralWidget(
        self,
        vartype: str
    ):

        if vartype not in self.literalWidgets:
            vartype = "String"
        self.literalStack.setCurrentWidget(self.literalWidgets[vartype])

    @Slot(int)
    def onCompTypeChanged(
        self,
        idx
    ):

        isVar = (self._compTypeCombo.currentData() == "variable")
        self.rhsStack.setCurrentIndex(1 if isVar else 0)
        if isVar:
            self.populateRhsVarCombo()


    def getLogic(
        self
    ) -> str:

        return self.logicCombo.currentData() if self.logicCombo else ""


    def toConditionText(
        self
    ) -> str:

        data = self.leftVarCombo.currentData()
        if not data:
            return ""
        name, vartype = data
        opSym = self.opCombo.currentData()
        isVarRef = (self._compTypeCombo.currentData() == "variable")
        if isVarRef:
            rd = self.rhsVarCombo.currentData()
            if rd:
                rhsName = rd[0]
                return f"{name} {opSym} {rhsName}"
            rhsText = self.rhsVarCombo.currentText().strip()
            if rhsText:
                return f"{name} {opSym} {rhsText}"
            return ""
        w = self.literalWidgets.get(vartype)
        if w:
            rawVal = getValueFromWidget(w)
            encoded = encodeValueStr(rawVal, vartype)
            return f"{name} {opSym} {encoded}"
        return ""


    def loadFromParts(
        self,
        operandName: str,
        opSym: str,
        valueExpr: str
    ):

        for ci in range(self.leftVarCombo.count()):
            d = self.leftVarCombo.itemData(ci)
            if d and d[0] == operandName:
                self.leftVarCombo.setCurrentIndex(ci)
                break
        if opSym:
            for oi in range(self.opCombo.count()):
                if self.opCombo.itemData(oi) == opSym:
                    self.opCombo.setCurrentIndex(oi)
                    break
        if not valueExpr:
            return
        up = valueExpr.strip().upper()
        data = self.leftVarCombo.currentData()
        vartype = data[1] if data else "String"
        if isVarReference(valueExpr) or self._isKnownVar(up):
            self._compTypeCombo.setCurrentIndex(1)
            self.populateRhsVarCombo()
            found = self._varMgr.findExactNameEntry(self.rhsVarCombo, up)
            if found >= 0:
                self.rhsVarCombo.setCurrentIndex(found)
            else:
                self.rhsVarCombo.addItem(up, (up, "String"))
                self.rhsVarCombo.setCurrentIndex(self.rhsVarCombo.count() - 1)
        else:
            self._compTypeCombo.setCurrentIndex(0)
            w = self.literalWidgets.get(vartype)
            if w:
                setWidgetValue(w, vartype, valueExpr)


    def _isKnownVar(
        self,
        name: str
    ) -> bool:

        return self._varMgr.getInfoByName(name) is not None


    def refreshVarCombos(
        self
    ):

        self.populateLeftVarCombo()
        self.populateRhsVarCombo()


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
        self.opTypeCombo = makeComboWidget(ACTION_TYPES, min_width=70, parent=self)
        layout.addWidget(self.opTypeCombo)
        layout.addWidget(makeLabel("设置", self))
        self.targetCombo = QComboBox(self)
        self.targetCombo.setFixedHeight(25)
        self.targetCombo.setMinimumWidth(120)
        self.buildTargetCombo()
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


    def buildTargetCombo(
        self
    ):

        self.targetCombo.blockSignals(True)
        self.targetCombo.clear()
        for p in PRESET_VARIABLES:
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
        for vt in VAR_TYPE_ORDER:
            self._literalWidgets[vt] = makeValueWidget(vt, self.valueStack)
            self.valueStack.addWidget(self._literalWidgets[vt])
            if vt in ARITH_TYPES:
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
        self.updateRHSWidget()
        self.onValueSrcChanged(self.valueSrcCombo.currentIndex())

    @Slot(int)
    def onOpTypeChanged(
        self,
        idx
    ):

        self.updateRHSWidget()


    def updateRHSWidget(
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
            self.updateRHSWidget()


    def getTargetName(
        self
    ) -> str:

        data = self.targetCombo.currentData()
        return data[0] if data else ""


    def toScriptLine(
        self
    ) -> str:

        target = self.getTargetName()
        if not target:
            return ""
        op = self.opTypeCombo.currentData()
        rawVal = self._getValueRaw()
        if op == "set":
            vartype = self._currentTargetType
            encoded = encodeValueStr(rawVal, vartype)
            if vartype == "Time":
                if rawVal.startswith("+"):
                    return f"    {target} .ADD. {rawVal[1:]}"
                if rawVal.startswith("-"):
                    return f"    {target} .SUB. {rawVal[1:]}"
            return f"    SET {target} = {encoded}"
        elif op == "add":
            vartype = self._currentTargetType
            if vartype == "Date" and hasattr(self.valueStack.currentWidget(), "getOffsetDays"):
                days = self.valueStack.currentWidget().getOffsetDays()
                return f"    {target} .ADD. {days}"
            if vartype == "Time" and hasattr(self.valueStack.currentWidget(), "getOffsetHours"):
                hours = self.valueStack.currentWidget().getOffsetHours()
                return f"    {target} .ADD. {hours}"
            return f"    {target} .ADD. {rawVal}"
        elif op == "sub":
            vartype = self._currentTargetType
            if vartype == "Date" and hasattr(self.valueStack.currentWidget(), "getOffsetDays"):
                days = self.valueStack.currentWidget().getOffsetDays()
                return f"    {target} .SUB. {days}"
            if vartype == "Time" and hasattr(self.valueStack.currentWidget(), "getOffsetHours"):
                hours = self.valueStack.currentWidget().getOffsetHours()
                return f"    {target} .SUB. {hours}"
            return f"    {target} .SUB. {rawVal}"
        return ""


    def _getValueRaw(
        self
    ) -> str:

        if self.valueSrcCombo.currentData() == "variable":
            return self.existingVarCombo.currentText().strip()
        w = self.valueStack.currentWidget()
        if w:
            return getValueFromWidget(w)
        return ""


    def setOpType(
        self,
        opType: str
    ):

        for i in range(self.opTypeCombo.count()):
            if self.opTypeCombo.itemData(i) == opType:
                self.opTypeCombo.setCurrentIndex(i)
                break


    def loadFromScript(
        self,
        targetVar: str,
        valueExpr: str
    ):

        targetUp = targetVar.upper().strip()
        for ci in range(self.targetCombo.count()):
            d = self.targetCombo.itemData(ci)
            if d and d[0] == targetUp:
                self.targetCombo.setCurrentIndex(ci)
                break
        self._setValueFromExpr(valueExpr)


    def _setValueFromExpr(
        self,
        expr: str
    ):

        s = expr.strip()
        if not s:
            return
        up = s.upper()
        if isVarReference(s):
            self.valueSrcCombo.setCurrentIndex(1)
            self._varMgr.populateCombo(self.existingVarCombo)
            idx = self._varMgr.findExactNameEntry(self.existingVarCombo, up)
            if idx >= 0:
                self.existingVarCombo.setCurrentIndex(idx)
            else:
                self.existingVarCombo.addItem(up, (up, "String"))
                self.existingVarCombo.setCurrentIndex(self.existingVarCombo.count() - 1)
        else:
            self.valueSrcCombo.setCurrentIndex(0)
            w = self.valueStack.currentWidget()
            if w:
                setWidgetValue(w, self._currentTargetType, expr)


    def refreshVarCombos(
        self
    ):

        currentData = self.targetCombo.currentData()
        self.buildTargetCombo()
        if currentData:
            for i in range(self.targetCombo.count()):
                d = self.targetCombo.itemData(i)
                if d and d[0] == currentData[0]:
                    self.targetCombo.setCurrentIndex(i)
                    break
        self._varMgr.populateCombo(self.existingVarCombo)
