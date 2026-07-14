# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
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
        self._var_mgr = VariableManager(self)

        self.setupUi()
        self.connectSignals()
        self.addBlock()
        self.ScrollLayout.addStretch()

    def setupUi(
        self
    ):

        self.setWindowTitle("AutoScript 指令编排 - AutoLibrary")
        self.setMinimumSize(640, 600)
        self.setModal(True)
        MainLayout = QVBoxLayout(self)
        Scroll = QScrollArea()
        Scroll.setWidgetResizable(True)
        Scroll.setFrameShape(QFrame.NoFrame)
        ScrollContent = QWidget()
        self.ScrollLayout = QVBoxLayout(ScrollContent)
        self.ScrollLayout.setSpacing(5)
        Scroll.setWidget(ScrollContent)
        MainLayout.addWidget(Scroll)
        self.AddBlockBtn = QPushButton("+ 添加判断块")
        self.AddBlockBtn.setFixedHeight(25)
        MainLayout.addWidget(self.AddBlockBtn)
        self.BtnBox = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        self.BtnBox.button(QDialogButtonBox.StandardButton.Ok).setText("确定")
        self.BtnBox.button(QDialogButtonBox.StandardButton.Cancel).setText("取消")
        MainLayout.addWidget(self.BtnBox)

    def connectSignals(
        self
    ):

        self.BtnBox.accepted.connect(self.onAccept)
        self.BtnBox.rejected.connect(self.reject)
        self.AddBlockBtn.clicked.connect(self.addBlock)

    def updateBlockTypeRestrictions(
        self
    ):

        prevType = None
        for block in self._blocks:
            block.setPrevBlockType(prevType)
            prevType = block.getBlockType()

    def addBlock(
        self
    ):

        Block = ConditionalBlock(
            len(self._blocks), self._var_mgr, parent=self
        )
        Block.DeleteBlockBtn.clicked.connect(lambda: self.removeBlock(Block))
        Block.TypeCombo.currentIndexChanged.connect(self.updateBlockTypeRestrictions)
        Block.addActionStep()
        self._blocks.append(Block)
        self.updateBlockTypeRestrictions()
        if self.ScrollLayout.count() > 0:
            lastItem = self.ScrollLayout.itemAt(
                self.ScrollLayout.count() - 1
            )
            if lastItem and lastItem.spacerItem():
                self.ScrollLayout.insertWidget(
                    self.ScrollLayout.count() - 1, Block
                )
                return
        self.ScrollLayout.addWidget(Block)

    def removeBlock(
        self,
        block: ConditionalBlock
    ):

        if len(self._blocks) <= 1:
            QMessageBox.information(self, "提示", "至少保留一个判断块。")
            return
        if block in self._blocks:
            self._blocks.remove(block)
            self.ScrollLayout.removeWidget(block)
            block.hide()
            block.deleteLater()
        for i, blk in enumerate(self._blocks):
            blk.blockIndex = i
            if i == 0:
                blk.TypeCombo.setEnabled(False)
                blk.TypeCombo.setCurrentIndex(0)
            else:
                blk.TypeCombo.setEnabled(True)
            blk.refreshVarCombos()
        self.updateBlockTypeRestrictions()

    def getScript(
        self
    ) -> str:
        """
            Generate the complete Lua script from all blocks.
        """

        parts = []
        prevType = None
        for block in self._blocks:
            blockType = block.getBlockType()
            if blockType == "IF" and prevType is not None:
                parts.append("end")
            lines = block.toScript()
            parts.extend(lines)
            prevType = blockType
        if self._blocks and self._blocks[0].getBlockType() == "IF":
            parts.append("end")
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
