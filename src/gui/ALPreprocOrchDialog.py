# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""

from PySide6.QtCore import QTime, QDate
from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QScrollArea, QTimeEdit,
    QDateEdit, QLineEdit, QSpinBox, QDoubleSpinBox,
    QStackedWidget, QFrame, QDialogButtonBox,
    QGroupBox, QSizePolicy
)

from utils.PreprocEngine import PreprocEngine


VARIABLE_META = PreprocEngine.VARIABLE_META

_VAR_COMBO_ITEMS = [
    (display, varname, vartype)
    for display, (varname, vartype) in VARIABLE_META.items()
]

_VAR_COMBO_ITEMS_SET = [
    (display, varname, vartype)
    for display, (varname, vartype) in VARIABLE_META.items()
    if not varname.startswith("CURRENT_")
]

OP_ITEMS = [
    ("等于", ".EQ."),
    ("不等于", ".NEQ."),
    ("大于", ".BGT."),
    ("小于", ".BLT."),
    ("大于等于", ".BGE."),
    ("小于等于", ".BLE."),
]


def _makeVarCombo(
) -> QComboBox:

    cb = QComboBox()
    for display, varname, vartype in _VAR_COMBO_ITEMS:
        cb.addItem(display, (varname, vartype))
    cb.setMinimumWidth(120)
    cb.setFixedHeight(25)
    return cb


def _makeSetVarCombo(
) -> QComboBox:

    cb = QComboBox()
    for display, varname, vartype in _VAR_COMBO_ITEMS_SET:
        cb.addItem(display, (varname, vartype))
    cb.setMinimumWidth(120)
    cb.setFixedHeight(25)
    return cb


def _makeOpCombo(
) -> QComboBox:

    cb = QComboBox()
    for display, op in OP_ITEMS:
        cb.addItem(display, op)
    cb.setMinimumWidth(80)
    cb.setFixedHeight(25)
    return cb


def _makeValueWidget(
    data_type: str
) -> QWidget:

    if data_type == "Time":
        w = QTimeEdit()
        w.setDisplayFormat("HH:mm")
        w.setMinimumWidth(100)
        w.setFixedHeight(25)
    elif data_type == "Date":
        w = QDateEdit()
        w.setDisplayFormat("yyyy-MM-dd")
        w.setCalendarPopup(True)
        w.setMinimumWidth(130)
        w.setFixedHeight(25)
    elif data_type == "Integer":
        w = QSpinBox()
        w.setMinimum(-999999)
        w.setMaximum(999999)
        w.setMinimumWidth(100)
        w.setFixedHeight(25)
    elif data_type == "Float":
        w = QDoubleSpinBox()
        w.setMinimum(-999999)
        w.setMaximum(999999)
        w.setDecimals(2)
        w.setMinimumWidth(100)
        w.setFixedHeight(25)
    elif data_type == "Boolean":
        w = QComboBox()
        w.addItem(".TRUE.", ".TRUE.")
        w.addItem(".FALSE.", ".FALSE.")
        w.setMinimumWidth(100)
        w.setFixedHeight(25)
    else:
        w = QLineEdit()
        w.setPlaceholderText("输入值")
        w.setMinimumWidth(120)
        w.setFixedHeight(25)
    return w


def _makeActionValueWidget(
    data_type: str
) -> QWidget:

    if data_type == "Date":
        w = QComboBox()
        w.addItem("今天", "today")
        w.addItem("明天", "tomorrow")
        w.setFixedHeight(25)
        w.setMinimumWidth(100)
        w._is_date_action = True
        return w

    if data_type == "Time":
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        modeCombo = QComboBox()
        modeCombo.addItem("固定时间", "fixed")
        modeCombo.addItem("相对当前", "relative")
        modeCombo.setFixedHeight(25)
        stack = QStackedWidget()
        timeEdit = QTimeEdit()
        timeEdit.setDisplayFormat("HH:mm")
        timeEdit.setFixedHeight(25)
        spinBox = QSpinBox()
        spinBox.setRange(0, 23)
        spinBox.setSuffix("小时")
        spinBox.setFixedHeight(25)
        stack.addWidget(timeEdit)
        stack.addWidget(spinBox)
        modeCombo.currentIndexChanged.connect(
            lambda i: stack.setCurrentIndex(i)
        )
        layout.addWidget(modeCombo)
        layout.addWidget(stack)
        container._modeCombo = modeCombo
        container._timeEdit = timeEdit
        container._spinBox = spinBox
        container._isActionTime = True
        return container

    return _makeValueWidget(data_type)


def _getValueFromWidget(
    w: QWidget
) -> str:

    if getattr(w, '_isActionTime', False):
        if w._modeCombo.currentData() == "fixed":
            return w._timeEdit.time().toString("HH:mm")
        else:
            return f"+{w._spinBox.value()}"
    if isinstance(w, QTimeEdit):
        return w.time().toString("HH:mm")
    if isinstance(w, QDateEdit):
        return w.date().toString("yyyy-MM-dd")
    if isinstance(w, QComboBox):
        return w.currentText()
    if isinstance(w, QSpinBox):
        return str(w.value())
    if isinstance(w, QDoubleSpinBox):
        return str(w.value())
    if isinstance(w, QLineEdit):
        return w.text()
    return ""


def _encodeValueStr(
    raw_value: str,
    data_type: str
) -> str:

    if data_type == "Time":
        if raw_value.startswith("+"):
            return raw_value
        return f"TIME({raw_value})"
    elif data_type == "Date":
        if raw_value == "今天":
            return "CURRENT_DATE"
        elif raw_value == "明天":
            return "CURRENT_DATE + 1"
        return f"DATE({raw_value})"
    elif data_type == "Boolean":
        return raw_value
    elif data_type == "String":
        escaped = raw_value.replace("'", "''")
        return f"'{escaped}'"
    else:
        return raw_value


def _setWidgetValue(
    w: QWidget,
    vartype: str,
    expr: str
):

    import re
    s = expr.strip()

    if getattr(w, '_isActionTime', False):
        timeMatch = re.match(r"TIME\((\d{1,2}:\d{2})\)", s, re.IGNORECASE)
        if timeMatch:
            w._modeCombo.setCurrentIndex(0)
            parts = timeMatch.group(1).split(":")
            w._timeEdit.setTime(QTime(int(parts[0]), int(parts[1])))
            return
        relMatch = re.match(r"^\+(\d+)$", s)
        if relMatch:
            w._modeCombo.setCurrentIndex(1)
            w._spinBox.setValue(int(relMatch.group(1)))
            return
        return
    if getattr(w, '_is_date_action', False) and isinstance(w, QComboBox):
        if s.upper() in ("CURRENT_DATE", "TODAY"):
            w.setCurrentIndex(0)
        elif s.upper() in ("CURRENT_DATE + 1", "TOMORROW"):
            w.setCurrentIndex(1)
        else:
            dateMatch = re.match(
                r"DATE\((\d{4}-\d{2}-\d{2})\)", s, re.IGNORECASE
            )
            if dateMatch:
                from datetime import datetime, timedelta
                dateStr = dateMatch.group(1)
                today = datetime.now().strftime("%Y-%m-%d")
                tomorrow = (
                    datetime.now() + timedelta(days=1)
                ).strftime("%Y-%m-%d")
                if dateStr == today:
                    w.setCurrentIndex(0)
                elif dateStr == tomorrow:
                    w.setCurrentIndex(1)
        return
    if vartype == "Time":
        m = re.match(r"TIME\((\d{1,2}:\d{2})\)", s, re.IGNORECASE)
        if m and isinstance(w, QTimeEdit):
            parts = m.group(1).split(":")
            w.setTime(QTime(int(parts[0]), int(parts[1])))
    elif vartype == "Date":
        m = re.match(r"DATE\((\d{4}-\d{2}-\d{2})\)", s, re.IGNORECASE)
        if m and isinstance(w, QDateEdit):
            parts = m.group(1).split("-")
            w.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
    elif vartype == "Boolean" and isinstance(w, QComboBox):
        for i in range(w.count()):
            if w.itemData(i) == s.upper():
                w.setCurrentIndex(i)
                break
    elif vartype == "Integer" and isinstance(w, QSpinBox):
        try:
            w.setValue(int(s))
        except ValueError:
            pass
    elif vartype == "Float" and isinstance(w, QDoubleSpinBox):
        try:
            w.setValue(float(s))
        except ValueError:
            pass
    elif isinstance(w, QLineEdit):
        inner = s
        if (inner.startswith("'") and inner.endswith("'")) or \
           (inner.startswith('"') and inner.endswith('"')):
            inner = inner[1:-1].replace("''", "'")
        w.setText(inner)


class ActionStepFrame(QFrame):

    def __init__(
        self,
        parent=None
    ):
        super().__init__(parent)

        self.setupUi()
        self.connectSignals()
        self._onTargetChanged(0)


    def setupUi(
        self
    ):

        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setFixedHeight(35)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        self.targetCombo = _makeSetVarCombo()
        self.valueWidgetStack = QStackedWidget()
        self.valueWidgetStack.setFixedHeight(25)
        self._initValueStack()

        setLabel = QLabel("设置")
        setLabel.setFixedHeight(25)
        layout.addWidget(setLabel)
        layout.addWidget(self.targetCombo)
        toLabel = QLabel("为")
        toLabel.setFixedHeight(25)
        layout.addWidget(toLabel)
        layout.addWidget(self.valueWidgetStack)

        self.deleteBtn = QPushButton("×")
        self.deleteBtn.setFixedSize(24, 25)
        self.deleteBtn.setStyleSheet("color: red; font-weight: bold;")
        layout.addWidget(self.deleteBtn)


    def connectSignals(
        self
    ):

        self.targetCombo.currentIndexChanged.connect(self._onTargetChanged)

    def _initValueStack(
        self
    ):

        self._valueWidgets = {}
        for _, _, vartype in _VAR_COMBO_ITEMS:
            if vartype not in self._valueWidgets:
                w = _makeActionValueWidget(vartype)
                self._valueWidgets[vartype] = w
                self.valueWidgetStack.addWidget(w)
        self.valueWidgetStack.setCurrentWidget(
            self._valueWidgets.get("String", self.valueWidgetStack.widget(0))
        )

    def _onTargetChanged(
        self,
        idx
    ):
        if idx < 0:
            return
        data = self.targetCombo.itemData(idx)
        if data:
            _, vartype = data
            w = self._valueWidgets.get(vartype)
            if w:
                self.valueWidgetStack.setCurrentWidget(w)

    def getTarget(
        self
    ) -> str:

        data = self.targetCombo.currentData()
        return data[0] if data else ""

    def getTargetType(
        self
    ) -> str:

        data = self.targetCombo.currentData()
        return data[1] if data else "String"

    def getValueRaw(
        self
    ) -> str:

        currentType = self.getTargetType()
        w = self._valueWidgets.get(currentType)
        if w:
            return _getValueFromWidget(w)
        return ""

    def toScriptLine(
        self
    ) -> str:

        target = self.getTarget()
        if not target:
            return ""
        rawVal = self.getValueRaw()
        targetType = self.getTargetType()
        encoded = _encodeValueStr(rawVal, targetType)
        if targetType == "Time" and rawVal.startswith("+"):
            hours = rawVal[1:]
            return f"    {target} .ADD. {hours}"
        return f"    SET {target} = {encoded}"

    def loadFromScript(
        self,
        targetVar: str,
        valueExpr: str
    ):

        for idx in range(self.targetCombo.count()):
            data = self.targetCombo.itemData(idx)
            if data and data[0] == targetVar:
                self.targetCombo.setCurrentIndex(idx)
                break
        self._setValueFromExpr(valueExpr)

    def _setValueFromExpr(
        self,
        expr: str
    ):

        targetType = self.getTargetType()
        w = self._valueWidgets.get(targetType)
        if not w:
            return
        _setWidgetValue(w, targetType, expr)


class ConditionalBlock(QGroupBox):

    def __init__(
        self,
        blockIndex: int,
        parent=None
    ):
        super().__init__(parent)

        self.blockIndex = blockIndex
        self._actionWidgets = []

        self.setupUi()
        self.connectSignals()
        self._onOperandChanged(0)


    def setupUi(
        self
    ):

        self.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #ccc; "
            "margin-top: 8px; padding-top: 8px; }"
        )
        self.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed
        )

        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(4)
        mainLayout.setContentsMargins(5, 5, 5, 5)

        headerLayout = QHBoxLayout()
        self.typeCombo = QComboBox()
        self.typeCombo.addItem("IF", "IF")
        self.typeCombo.addItem("ELSE IF", "ELSE IF")
        self.typeCombo.addItem("ELSE", "ELSE")
        if self.blockIndex == 0:
            self.typeCombo.setEnabled(False)
        typeLabel = QLabel("类型:")
        typeLabel.setFixedHeight(25)
        headerLayout.addWidget(typeLabel)
        headerLayout.addWidget(self.typeCombo)
        headerLayout.addStretch()
        self.deleteBlockBtn = QPushButton("删除此块")
        self.deleteBlockBtn.setStyleSheet("color: red;")
        self.deleteBlockBtn.setFixedHeight(25)
        headerLayout.addWidget(self.deleteBlockBtn)
        mainLayout.addLayout(headerLayout)

        self.conditionWidget = QWidget()
        self.conditionWidget.setFixedHeight(60)
        condLayout = QHBoxLayout(self.conditionWidget)
        condLayout.setContentsMargins(0, 0, 0, 0)
        ifLabel = QLabel("如果")
        ifLabel.setFixedHeight(25)
        condLayout.addWidget(ifLabel)
        self.operandCombo = _makeVarCombo()
        condLayout.addWidget(self.operandCombo)
        self.opCombo = _makeOpCombo()
        condLayout.addWidget(self.opCombo)

        self.condValueStack = QStackedWidget()
        self.condValueStack.setFixedHeight(25)
        self._condValueWidgets = {}
        for vartype in ["Time", "Date", "String", "Integer", "Float", "Boolean"]:
            w = _makeValueWidget(vartype)
            self._condValueWidgets[vartype] = w
            self.condValueStack.addWidget(w)
        self.condValueStack.setCurrentWidget(self._condValueWidgets.get("String"))
        condLayout.addWidget(self.condValueStack)
        mainLayout.addWidget(self.conditionWidget)

        self.actionLabel = QLabel("执行步骤:")
        self.actionLabel.setFixedHeight(25)
        mainLayout.addWidget(self.actionLabel)

        self.actionsLayout = QVBoxLayout()
        self.actionsLayout.setSpacing(2)
        mainLayout.addLayout(self.actionsLayout)

        self.addActionBtn = QPushButton("+ 添加执行步骤")
        self.addActionBtn.setFixedHeight(25)
        mainLayout.addWidget(self.addActionBtn)


    def connectSignals(
        self
    ):

        self.operandCombo.currentIndexChanged.connect(self._onOperandChanged)
        self.typeCombo.currentIndexChanged.connect(self._onTypeChanged)
        self.addActionBtn.clicked.connect(self._addActionStep)

    def _onOperandChanged(
        self,
        idx
    ):
        if idx < 0:
            return
        data = self.operandCombo.itemData(idx)
        if data:
            _, vartype = data
            w = self._condValueWidgets.get(vartype)
            if w:
                self.condValueStack.setCurrentWidget(w)

    def _onTypeChanged(
        self,
        idx
    ):
        isCond = self.typeCombo.currentData() in ("IF", "ELSE IF")
        self.conditionWidget.setVisible(isCond)
        self.actionLabel.setText("执行步骤:" if isCond else "ELSE 执行步骤:")

    def _addActionStep(
        self
    ):

        step = ActionStepFrame(self)
        step.deleteBtn.clicked.connect(lambda: self._removeActionStep(step))
        self._actionWidgets.append(step)
        self.actionsLayout.addWidget(step)

    def _removeActionStep(
        self,
        step: ActionStepFrame
    ):

        if step in self._actionWidgets:
            self._actionWidgets.remove(step)
            self.actionsLayout.removeWidget(step)
            step.hide()
            step.deleteLater()

    def getBlockType(
        self
    ) -> str:

        return self.typeCombo.currentData()

    def toScriptLines(
        self
    ) -> list:

        blockType = self.getBlockType()
        lines = []

        if blockType in ("IF", "ELSE IF"):
            operand = self.operandCombo.currentData()
            operandName = operand[0] if operand else ""
            operandType = operand[1] if operand else "String"
            opSym = self.opCombo.currentData()
            rawVal = _getValueFromWidget(
                self._condValueWidgets.get(operandType, QLineEdit())
            )
            encodedVal = _encodeValueStr(rawVal, operandType)
            if blockType == "IF":
                lines.append(f"IF({operandName} {opSym} {encodedVal}) THEN")
            else:
                lines.append(f"ELSE IF({operandName} {opSym} {encodedVal}) THEN")
        else:
            lines.append("ELSE")
        for step in self._actionWidgets:
            scriptLine = step.toScriptLine()
            if scriptLine:
                lines.append(scriptLine)

        return lines

    def getConditionSummary(
        self
    ) -> str:

        bt = self.getBlockType()
        if bt == "ELSE":
            return "ELSE"
        operandData = self.operandCombo.currentData()
        if not operandData:
            return bt
        operandDisplay = self.operandCombo.currentText()
        opDisplay = self.opCombo.currentText()
        rawVal = self.getConditionRawValuePreview()
        return f"{bt} ({operandDisplay} {opDisplay} {rawVal})"

    def getConditionRawValuePreview(
        self
    ) -> str:

        data = self.operandCombo.currentData()
        if not data:
            return ""
        _, vartype = data
        w = self._condValueWidgets.get(vartype)
        if w:
            return _getValueFromWidget(w)
        return ""

    def countActionSteps(
        self
    ) -> int:

        return len(self._actionWidgets)


class ALPreprocOrchDialog(QDialog):

    def __init__(
        self,
        parent=None,
        existingScript: str = ""
    ):
        super().__init__(parent)
        self._blocks: list[ConditionalBlock] = []

        self.modifyUi()
        self.connectSignals()

        if existingScript and existingScript.strip():
            self._loadFromScript(existingScript)
        else:
            self._addBlock()
        self._scrollLayout.addStretch()


    def modifyUi(
        self
    ):

        self.setWindowTitle("预处理指令编排 - AutoLibrary")
        self.setMinimumSize(420, 400)
        self.setModal(True)
        mainLayout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scrollContent = QWidget()
        self._scrollLayout = QVBoxLayout(scrollContent)
        self._scrollLayout.setSpacing(5)
        scroll.setWidget(scrollContent)
        mainLayout.addWidget(scroll)
        addBlockLayout = QHBoxLayout()
        self.addBlockBtn = QPushButton("+ 添加判断块")
        self.addBlockBtn.setFixedHeight(25)
        addBlockLayout.addStretch()
        addBlockLayout.addWidget(self.addBlockBtn)
        addBlockLayout.addStretch()
        mainLayout.addLayout(addBlockLayout)
        self.btnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.btnBox.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        self.btnBox.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        mainLayout.addWidget(self.btnBox)


    def connectSignals(
        self
    ):

        self.btnBox.accepted.connect(self.accept)
        self.btnBox.rejected.connect(self.reject)
        self.addBlockBtn.clicked.connect(self._addBlock)

    def _addBlock(
        self
    ):

        block = ConditionalBlock(len(self._blocks), self)
        block.deleteBlockBtn.clicked.connect(lambda: self._removeBlock(block))
        self._blocks.append(block)
        block._addActionStep()
        if self._scrollLayout.count() > 0:
            lastItem = self._scrollLayout.itemAt(
                self._scrollLayout.count() - 1
            )
            if lastItem and lastItem.spacerItem():
                self._scrollLayout.insertWidget(
                    self._scrollLayout.count() - 1, block
                )
                return
        self._scrollLayout.addWidget(block)

    def _removeBlock(
        self,
        block: ConditionalBlock
    ):

        if block in self._blocks:
            self._blocks.remove(block)
            self._scrollLayout.removeWidget(block)
            block.hide()
            block.deleteLater()

    def getScript(
        self
    ) -> str:

        parts = []
        for i, block in enumerate(self._blocks):
            blockType = block.getBlockType()
            if blockType == "IF" and i > 0:
                parts.append("ENDIF")
            lines = block.toScriptLines()
            parts.extend(lines)
        if self._blocks and self._blocks[0].getBlockType() == "IF":
            parts.append("ENDIF")
        return "\n".join(parts)

    def getScriptPreview(
        self
    ) -> str:

        s = self.getScript()
        if len(s) > 10:
            return s[:7] + "..."
        return s

    def _loadFromScript(
        self,
        script: str
    ):

        import re
        lines = [l.strip() for l in script.split("\n") if l.strip()]
        if not lines:
            self._addBlock()
            return

        currentBlock = None
        currentBlockType = None
        actionsBuffer = []

        def flushBlock():
            nonlocal currentBlock, currentBlockType, actionsBuffer
            if currentBlock is None:
                return
            typeIdxMap = {"IF": 0, "ELSE IF": 1, "ELSE": 2}
            idx = typeIdxMap.get(currentBlockType, 0)
            currentBlock.typeCombo.setCurrentIndex(idx)
            currentBlock._onTypeChanged(idx)
            for oldStep in list(currentBlock._actionWidgets):
                currentBlock._removeActionStep(oldStep)
            for target, valueExpr in actionsBuffer:
                currentBlock._addActionStep()
                step = currentBlock._actionWidgets[-1]
                step.loadFromScript(target, valueExpr)
        self._blocks.clear()
        while self._scrollLayout.count():
            item = self._scrollLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for line in lines:
            upper = line.upper()
            ifMatch = re.match(r"^IF\((.+)\)\s*THEN\s*$", upper)
            if ifMatch:
                flushBlock()
                currentBlockType = "IF"
                actionsBuffer = []
                self._addBlock()
                currentBlock = self._blocks[-1]
                self._parseConditionToBlock(currentBlock, ifMatch.group(1))
                continue
            elifIfMatch = re.match(r"^ELSE\s+IF\((.+)\)\s*THEN\s*$", upper)
            if elifIfMatch:
                flushBlock()
                currentBlockType = "ELSE IF"
                actionsBuffer = []
                self._addBlock()
                currentBlock = self._blocks[-1]
                self._parseConditionToBlock(currentBlock, elifIfMatch.group(1))
                continue
            if upper == "ELSE":
                flushBlock()
                currentBlockType = "ELSE"
                actionsBuffer = []
                self._addBlock()
                currentBlock = self._blocks[-1]
                currentBlock.conditionWidget.setVisible(False)
                continue
            setMatch = re.match(r"^SET\s+(\w+)\s*=\s*(.+)$", line, re.IGNORECASE)
            if setMatch:
                target = setMatch.group(1).strip()
                valueExpr = setMatch.group(2).strip()
                actionsBuffer.append((target, valueExpr))
                continue
            addMatch = re.match(r"^(\w+)\s+\.ADD\.\s+(\d+)$", line, re.IGNORECASE)
            if addMatch:
                target = addMatch.group(1).strip()
                hours = addMatch.group(2).strip()
                actionsBuffer.append((target, f"+{hours}"))
                continue
            if upper in ("ENDIF", "END IF"):
                flushBlock()
                currentBlock = None
                currentBlockType = None
                actionsBuffer = []
                continue
        flushBlock()
        if not self._blocks:
            self._addBlock()

    def _parseConditionToBlock(
        self,
        block: ConditionalBlock,
        condStr: str
    ):

        condStr = condStr.strip()
        for _, opSym in OP_ITEMS:
            idx = condStr.upper().find(opSym)
            if idx >= 0:
                leftPart = condStr[:idx].strip()
                rightPart = condStr[idx + len(opSym):].strip()
                for ci in range(block.operandCombo.count()):
                    data = block.operandCombo.itemData(ci)
                    if data and data[0] == leftPart:
                        block.operandCombo.setCurrentIndex(ci)
                        break
                for oi in range(block.opCombo.count()):
                    if block.opCombo.itemData(oi) == opSym:
                        block.opCombo.setCurrentIndex(oi)
                        break
                opData = block.operandCombo.currentData()
                vartype = opData[1] if opData else "String"
                w = block._condValueWidgets.get(vartype)
                if w:
                    _setWidgetValue(w, vartype, rightPart)
                return
