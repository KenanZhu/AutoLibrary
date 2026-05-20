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

from gui.ALAutoScriptOrchDialog._helpers import VariableManager
from gui.ALAutoScriptOrchDialog._blocks import ConditionalBlock


class ALAutoScriptOrchDialog(QDialog):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._blocks = []
        self._varMgr = VariableManager(self)

        self.setupUi()
        self.connectSignals()
        self.addBlock()
        self.scrollLayout.addStretch()


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
        self.scrollLayout = QVBoxLayout(scrollContent)
        self.scrollLayout.setSpacing(5)
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
        if self.scrollLayout.count() > 0:
            lastItem = self.scrollLayout.itemAt(
                self.scrollLayout.count() - 1
            )
            if lastItem and lastItem.spacerItem():
                self.scrollLayout.insertWidget(
                    self.scrollLayout.count() - 1, block
                )
                return
        self.scrollLayout.addWidget(block)


    def removeBlock(
        self,
        block: ConditionalBlock
    ):

        if len(self._blocks) <= 1:
            QMessageBox.information(self, "提示", "至少保留一个判断块。")
            return
        if block in self._blocks:
            self._blocks.remove(block)
            self.scrollLayout.removeWidget(block)
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
                parts.append("END IF")
            lines = block.toScriptLines()
            parts.extend(lines)
            prevType = blockType
        if self._blocks and self._blocks[0].getBlockType() == "IF":
            parts.append("END IF")
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
