"""
Orchestration dialog for visually composing AutoScript scripts.
"""
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from gui.ALAutoScriptOrchDialog._precheck import precheck
from gui.ALAutoScriptOrchDialog._orchestrate import parseBlocks

from gui.ALAutoScriptOrchDialog._helpers import (
    COMPARE_OPERATORS,
    PRESET_NAMES,
    VariableManager,
    findOperatorIn,
    splitTopLevel,
    stripOuterParens,
)
from gui.ALAutoScriptOrchDialog._blocks import ConditionalBlock
from gui.ALAutoScriptOrchDialog._widgets import ConditionRowFrame


class ALAutoScriptOrchDialog(QDialog):

    def __init__(
        self,
        parent = None,
        existingScript: str = ""
    ):

        super().__init__(parent)
        self._blocks = []
        self._varMgr = VariableManager(self)

        self.setupUi()
        self.connectSignals()
        if existingScript and existingScript.strip():
            self.loadFromScript(existingScript)
        else:
            self.addBlock()
        self._scrollLayout.addStretch()


    def setupUi(
        self
    ):

        self.setWindowTitle("AutoScript 指令编排 - AutoLibrary")
        self.setMinimumSize(640, 600)
        self.setModal(True)
        mainLayout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scrollContent = QWidget()
        self._scrollLayout = QVBoxLayout(scrollContent)
        self._scrollLayout.setSpacing(5)
        scroll.setWidget(scrollContent)
        mainLayout.addWidget(scroll)
        self.addBlockBtn = QPushButton("+ 添加判断块")
        self.addBlockBtn.setFixedHeight(25)
        mainLayout.addWidget(self.addBlockBtn)
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

        self.btnBox.accepted.connect(self.onAccept)
        self.btnBox.rejected.connect(self.reject)
        self.addBlockBtn.clicked.connect(self.addBlock)


    def _updateBlockTypeRestrictions(
        self
    ):

        prevType = None
        for block in self._blocks:
            block.setPrevBlockType(prevType)
            prevType = block.getBlockType()


    def addBlock(
        self
    ):

        block = ConditionalBlock(
            len(self._blocks), self._varMgr, parent=self
        )
        block.deleteBlockBtn.clicked.connect(lambda: self.removeBlock(block))
        block.typeCombo.currentIndexChanged.connect(self._updateBlockTypeRestrictions)
        block.addActionStep()
        self._blocks.append(block)
        self._updateBlockTypeRestrictions()
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


    def removeBlock(
        self,
        block: ConditionalBlock
    ):

        if len(self._blocks) <= 1:
            QMessageBox.information(self, "提示", "至少保留一个判断块。")
            return
        if block in self._blocks:
            self._blocks.remove(block)
            self._scrollLayout.removeWidget(block)
            block.hide()
            block.deleteLater()
        for i, blk in enumerate(self._blocks):
            blk.blockIndex = i
            if i == 0:
                blk.typeCombo.setEnabled(False)
                blk.typeCombo.setCurrentIndex(0)
            else:
                blk.typeCombo.setEnabled(True)
            blk.refreshVarCombos()
        self._updateBlockTypeRestrictions()


    def getScript(
        self
    ) -> str:

        parts = []
        prevType = None
        for block in self._blocks:
            blockType = block.getBlockType()
            if blockType == "IF" and prevType is not None:
                parts.append("ENDIF")
            lines = block.toScriptLines()
            parts.extend(lines)
            prevType = blockType
        if self._blocks and self._blocks[0].getBlockType() == "IF":
            parts.append("ENDIF")
        return "\n".join(parts)

    @Slot()
    def onAccept(
        self
    ):

        script = self.getScript().strip()
        if not script:
            QMessageBox.warning(self, "提示", "脚本内容为空，请添加至少一个操作步骤。")
            return
        self.accept()

    @staticmethod
    def precheckScriptForOrchestration(
        script: str
    ) -> tuple[bool, str]:

        return precheck(script, allowed_vars=PRESET_NAMES)

    def loadFromScript(
        self,
        script: str
    ):

        if not script.strip():
            self.addBlock()
            return
        ok, err = self.precheckScriptForOrchestration(script)
        if not ok:
            QMessageBox.warning(
                self, "无法编排",
                f"脚本检查失败:\n{err}\n\n"
                "请通过\"编辑\"按钮打开脚本编辑窗口进行修改。"
            )
            self.addBlock()
            return
        # Structured block data via observer-based parsing — no duplicate logic
        typeIdxMap = {"IF": 0, "ELSE IF": 1, "ELSE": 2}
        parsedBlocks = parseBlocks(script)
        self._blocks.clear()
        while self._scrollLayout.count():
            item = self._scrollLayout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        try:
            for blockType, condition, actions in parsedBlocks:
                self.addBlock()
                block = self._blocks[-1]
                idx = typeIdxMap.get(blockType, 0)
                block.typeCombo.setCurrentIndex(idx)
                block.onTypeChanged(idx)
                for oldStep in list(block._actionWidgets):
                    block.removeActionStep(oldStep)
                for target, valueExpr, opType in actions:
                    block.addActionStep()
                    step = block.getActionSteps()[-1]
                    step.setOpType(opType)
                    step.loadFromScript(target, valueExpr)
                if blockType in ("IF", "ELSE IF") and condition:
                    self._parseConditions(block, condition)
        except Exception:
            self._blocks.clear()
            while self._scrollLayout.count():
                item = self._scrollLayout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
        self._updateBlockTypeRestrictions()
        if not self._blocks:
            self.addBlock()


    def _parseConditions(
        self,
        block: ConditionalBlock,
        condStr: str
    ):

        s = condStr.strip()
        if not s:
            return
        s = stripOuterParens(s)
        orParts = splitTopLevel(s, ".OR.")
        allSubConds = []
        allLogics = []
        for pi, part in enumerate(orParts):
            part = part.strip()
            if pi > 0:
                allLogics.append(".OR.")
            andParts = splitTopLevel(part, ".AND.")
            for ai, ap in enumerate(andParts):
                ap = ap.strip()
                if ai > 0:
                    allLogics.append(".AND.")
                allSubConds.append(ap)
        for row in list(block._conditionRows):
            block._condRowsLayout.removeWidget(row)
            row.hide()
            row.deleteLater()
        block._conditionRows.clear()
        for i, subCond in enumerate(allSubConds):
            subCond = subCond.strip()
            subCond = stripOuterParens(subCond)
            isFirst = (i == 0)
            row = ConditionRowFrame(
                self._varMgr, block.blockIndex,
                isFirst=isFirst, parent=block
            )
            if not isFirst:
                row.deleteBtn.clicked.connect(
                    lambda _checked=False, r=row: block.removeConditionRow(r)
                )
                if i - 1 < len(allLogics):
                    logic = allLogics[i - 1]
                    for li in range(row.logicCombo.count()):
                        if row.logicCombo.itemData(li) == logic:
                            row.logicCombo.setCurrentIndex(li)
                            break
            block._conditionRows.append(row)
            block._condRowsLayout.addWidget(row)
            subUp = subCond.upper()
            if subUp in (".TRUE.", ".FALSE."):
                row.loadFromParts(subUp, "", "")
            else:
                opSyms = [op for _, op in COMPARE_OPERATORS]
                result = findOperatorIn(subCond, opSyms)
                if result:
                    idx, op = result
                    leftPart = subCond[:idx].strip()
                    rightPart = subCond[idx + len(op):].strip()
                    row.loadFromParts(leftPart, op, rightPart)
                else:
                    row.loadFromParts(subCond, "", "")
        if not block._conditionRows:
            block.addInitialConditionRow()
