# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
"""
    Conditional block widget for the AutoScript orchestration dialog.
"""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from gui.ALAutoScriptOrchDialog._widgets import (
    ActionStepFrame,
    ConditionRowFrame,
)


class ConditionalBlock(QGroupBox):

    def __init__(
        self,
        blockIndex: int,
        varMgr = None,
        parent = None
    ):

        super().__init__(parent)
        self.blockIndex = blockIndex
        self._varMgr = varMgr
        self._actionWidgets = []
        self._conditionRows = []

        self.setupUi()
        self.connectSignals()
        self.addInitialConditionRow()

    def setupUi(
        self
    ):

        self.setUpdatesEnabled(False)
        self.setStyleSheet(
            "QGroupBox { font-weight: bold; border: 1px solid #ccc; "
            "margin-top: 5px; padding-top: 5px; }"
        )
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        mainLayout = QVBoxLayout(self)
        mainLayout.setSpacing(6)
        mainLayout.setContentsMargins(8, 8, 8, 8)
        headerLayout = QHBoxLayout()
        headerLayout.setSpacing(8)
        self.typeCombo = QComboBox(self)
        self.typeCombo.addItem("IF", "IF")
        self.typeCombo.addItem("ELSE IF", "ELSE IF")
        self.typeCombo.addItem("ELSE", "ELSE")
        self.typeCombo.setFixedHeight(25)
        if self.blockIndex == 0:
            self.typeCombo.setEnabled(False)
        headerLayout.addWidget(QLabel("类型:", self))
        headerLayout.addWidget(self.typeCombo)
        headerLayout.addStretch()
        self.deleteBlockBtn = QPushButton("删除此块", self)
        self.deleteBlockBtn.setStyleSheet("color: red;")
        self.deleteBlockBtn.setFixedHeight(25)
        headerLayout.addWidget(self.deleteBlockBtn)
        mainLayout.addLayout(headerLayout)
        self.conditionWidget = QWidget(self)
        self.conditionWidget.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred
        )
        condLayout = QVBoxLayout(self.conditionWidget)
        condLayout.setContentsMargins(4, 4, 4, 4)
        condLayout.setSpacing(6)
        self.condRowsLayout = QVBoxLayout()
        self.condRowsLayout.setSpacing(4)
        condLayout.addLayout(self.condRowsLayout)
        self.addCondBtn = QPushButton("+ 添加条件", self.conditionWidget)
        self.addCondBtn.setFixedHeight(25)
        condLayout.addWidget(self.addCondBtn)
        mainLayout.addWidget(self.conditionWidget)
        self.actionLabel = QLabel("执行步骤:", self)
        self.actionLabel.setFixedHeight(25)
        mainLayout.addWidget(self.actionLabel)
        self.actionsLayout = QVBoxLayout()
        self.actionsLayout.setSpacing(4)
        mainLayout.addLayout(self.actionsLayout)
        self.addActionBtn = QPushButton("+ 添加执行步骤", self)
        self.addActionBtn.setFixedHeight(25)
        mainLayout.addWidget(self.addActionBtn)
        self.setUpdatesEnabled(True)

    def connectSignals(
        self
    ):

        self.typeCombo.currentIndexChanged.connect(self.onTypeChanged)
        self.addCondBtn.clicked.connect(self.addConditionRow)
        self.addActionBtn.clicked.connect(self.addActionStep)

    def addInitialConditionRow(
        self
    ):

        row = ConditionRowFrame(
            self._varMgr, self.blockIndex,
            isFirst=True, parent=self
        )
        self._conditionRows.append(row)
        self.condRowsLayout.addWidget(row)

    def addConditionRow(
        self
    ):

        row = ConditionRowFrame(
            self._varMgr, self.blockIndex,
            isFirst=False, parent=self
        )
        row.deleteBtn.clicked.connect(lambda: self.removeConditionRow(row))
        self._conditionRows.append(row)
        self.condRowsLayout.addWidget(row)

    def removeConditionRow(
        self,
        row: ConditionRowFrame
    ):

        if row in self._conditionRows and len(self._conditionRows) > 1:
            self._conditionRows.remove(row)
            self.condRowsLayout.removeWidget(row)
            row.hide()
            row.deleteLater()

    def addActionStep(
        self
    ):

        step = ActionStepFrame(self._varMgr, self.blockIndex, parent=self)
        step.deleteBtn.clicked.connect(lambda: self.removeActionStep(step))
        self._actionWidgets.append(step)
        self.actionsLayout.addWidget(step)

    def removeActionStep(
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

    def getConditionRows(
        self
    ):

        return list(self._conditionRows)

    def getActionSteps(
        self
    ):

        return list(self._actionWidgets)

    def countActionSteps(
        self
    ) -> int:

        return len(self._actionWidgets)

    def toScript(
        self
    ) -> list:
        """
            Generate Lua script lines for this conditional block.
        """

        blockType = self.getBlockType()
        lines = []
        if blockType in ("IF", "ELSE IF"):
            condTexts = [
                r.toScript() for r in self._conditionRows if r.toScript()
            ]
            if not condTexts:
                condTexts = ["true"]

            if len(condTexts) == 1:
                combined = condTexts[0]
            else:
                parts = []
                for i, ct in enumerate(condTexts):
                    if i > 0:
                        logic = self._conditionRows[i].getLogic() or "and"
                        parts.append(f" {logic} ")
                    parts.append(f"({ct})")
                combined = "".join(parts)
            if blockType == "IF":
                lines.append(f"if {combined} then")
            else:
                lines.append(f"elseif {combined} then")
        else:
            lines.append("else")
        for step in self._actionWidgets:
            scriptLine = step.toScript()
            if scriptLine:
                lines.append(scriptLine)
        return lines

    def refreshVarCombos(
        self
    ):

        for row in self._conditionRows:
            row.refreshVarCombos()
        for step in self._actionWidgets:
            step.refreshVarCombos()

    def setPrevBlockType(
        self,
        prevType: str | None
    ):

        model = self.typeCombo.model()
        if model is None:
            return
        for data in ("ELSE IF", "ELSE"):
            idx = self.typeCombo.findData(data)
            if idx < 0:
                continue
            item = model.item(idx)
            shouldEnable = prevType != "ELSE"
            item.setEnabled(shouldEnable)
        if prevType == "ELSE" and self.typeCombo.currentData() in ("ELSE IF", "ELSE"):
            self.typeCombo.setCurrentIndex(0)

    @Slot(int)
    def onTypeChanged(
        self,
        _idx
    ):

        isCond = self.typeCombo.currentData() in ("IF", "ELSE IF")
        self.conditionWidget.setVisible(isCond)
        self.actionLabel.setText(
            "执行步骤:" if isCond else "ELSE 执行步骤:"
        )
