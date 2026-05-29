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
        MainLayout = QVBoxLayout(self)
        MainLayout.setSpacing(6)
        MainLayout.setContentsMargins(8, 8, 8, 8)
        HeaderLayout = QHBoxLayout()
        HeaderLayout.setSpacing(8)
        self.TypeCombo = QComboBox(self)
        self.TypeCombo.addItem("IF", "IF")
        self.TypeCombo.addItem("ELSE IF", "ELSE IF")
        self.TypeCombo.addItem("ELSE", "ELSE")
        self.TypeCombo.setFixedHeight(25)
        if self.blockIndex == 0:
            self.TypeCombo.setEnabled(False)
        HeaderLayout.addWidget(QLabel("类型:", self))
        HeaderLayout.addWidget(self.TypeCombo)
        HeaderLayout.addStretch()
        self.DeleteBlockBtn = QPushButton("删除此块", self)
        self.DeleteBlockBtn.setStyleSheet("color: red;")
        self.DeleteBlockBtn.setFixedHeight(25)
        HeaderLayout.addWidget(self.DeleteBlockBtn)
        MainLayout.addLayout(HeaderLayout)
        self.ConditionWidget = QWidget(self)
        self.ConditionWidget.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Preferred
        )
        CondLayout = QVBoxLayout(self.ConditionWidget)
        CondLayout.setContentsMargins(4, 4, 4, 4)
        CondLayout.setSpacing(6)
        self.CondRowsLayout = QVBoxLayout()
        self.CondRowsLayout.setSpacing(4)
        CondLayout.addLayout(self.CondRowsLayout)
        self.AddCondBtn = QPushButton("+ 添加条件", self.ConditionWidget)
        self.AddCondBtn.setFixedHeight(25)
        CondLayout.addWidget(self.AddCondBtn)
        MainLayout.addWidget(self.ConditionWidget)
        self.ActionLabel = QLabel("执行步骤:", self)
        self.ActionLabel.setFixedHeight(25)
        MainLayout.addWidget(self.ActionLabel)
        self.ActionsLayout = QVBoxLayout()
        self.ActionsLayout.setSpacing(4)
        MainLayout.addLayout(self.ActionsLayout)
        self.AddActionBtn = QPushButton("+ 添加执行步骤", self)
        self.AddActionBtn.setFixedHeight(25)
        MainLayout.addWidget(self.AddActionBtn)
        self.setUpdatesEnabled(True)

    def connectSignals(
        self
    ):

        self.TypeCombo.currentIndexChanged.connect(self.onTypeChanged)
        self.AddCondBtn.clicked.connect(self.addConditionRow)
        self.AddActionBtn.clicked.connect(self.addActionStep)

    def addInitialConditionRow(
        self
    ):

        Row = ConditionRowFrame(
            self._varMgr, self.blockIndex,
            isFirst=True, parent=self
        )
        self._conditionRows.append(Row)
        self.CondRowsLayout.addWidget(Row)

    def addConditionRow(
        self
    ):

        Row = ConditionRowFrame(
            self._varMgr, self.blockIndex,
            isFirst=False, parent=self
        )
        Row.DeleteBtn.clicked.connect(lambda: self.removeConditionRow(Row))
        self._conditionRows.append(Row)
        self.CondRowsLayout.addWidget(Row)

    def removeConditionRow(
        self,
        row: ConditionRowFrame
    ):

        if row in self._conditionRows and len(self._conditionRows) > 1:
            self._conditionRows.remove(row)
            self.CondRowsLayout.removeWidget(row)
            row.hide()
            row.deleteLater()

    def addActionStep(
        self
    ):

        Step = ActionStepFrame(self._varMgr, self.blockIndex, parent=self)
        Step.DeleteBtn.clicked.connect(lambda: self.removeActionStep(Step))
        self._actionWidgets.append(Step)
        self.ActionsLayout.addWidget(Step)

    def removeActionStep(
        self,
        step: ActionStepFrame
    ):

        if step in self._actionWidgets:
            self._actionWidgets.remove(step)
            self.ActionsLayout.removeWidget(step)
            step.hide()
            step.deleteLater()

    def getBlockType(
        self
    ) -> str:

        return self.TypeCombo.currentData()

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

        model = self.TypeCombo.model()
        if model is None:
            return
        for data in ("ELSE IF", "ELSE"):
            idx = self.TypeCombo.findData(data)
            if idx < 0:
                continue
            item = model.item(idx)
            shouldEnable = prevType != "ELSE"
            item.setEnabled(shouldEnable)
        if prevType == "ELSE" and self.TypeCombo.currentData() in ("ELSE IF", "ELSE"):
            self.TypeCombo.setCurrentIndex(0)

    @Slot(int)
    def onTypeChanged(
        self,
        _idx
    ):

        isCond = self.TypeCombo.currentData() in ("IF", "ELSE IF")
        self.ConditionWidget.setVisible(isCond)
        self.ActionLabel.setText(
            "执行步骤:" if isCond else "ELSE 执行步骤:"
        )
