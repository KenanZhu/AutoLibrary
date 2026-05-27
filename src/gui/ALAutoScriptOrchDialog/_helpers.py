# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
"""
    Helper utilities and constants for the AutoScript orchestration dialog.
"""
import re

from PySide6.QtCore import QObject
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpinBox,
    QStackedWidget,
    QTimeEdit,
    QWidget,
)

from autoscript import createAllVariablesTable

VARTYPE_INFOS = [
    # varType, isArithType
    ("String",  False),
    ("Int",     True),
    ("Float",   True),
    ("Boolean", False),
    ("Date",    True),
    ("Time",    True),
]


def getTypeOrder(
) -> list:

    return [t for t, _ in VARTYPE_INFOS]

def getArithType(
    varType: str
) -> bool:

    for t, a in VARTYPE_INFOS:
        if t == varType:
            return a

def getPresetVars(
) -> list:

    return [
        {"name": name.upper(), "type": vtype, "display": display}
        for display, (name, vtype) in createAllVariablesTable().items()
    ]


COMPARE_OPTIONS = [
    ("等于", "=="),
    ("不等于", "~="),
    ("大于", ">"),
    ("小于", "<"),
    ("大于等于", ">="),
    ("小于等于", "<="),
]
LOGIC_OPTIONS = [
    ("并且 (and)", "and"),
    ("或者 (or)", "or"),
]
ACTION_OPTIONS = [
    ("设置为", "set"),
    ("增加", "add"),
    ("减少", "sub"),
]
DATE_OPTIONS = [
    ("前天", "day_before_yesterday"),
    ("昨天", "yesterday"),
    ("今天", "today"),
    ("明天", "tomorrow"),
    ("后天", "day_after_tomorrow")
]
DATE_OFFSET_OPTIONS = [
    ("天", "days"),
    ("周", "weeks"),
    # NOTE: "月" and "年" use fixed day counts (30 / 365), not calendar months/years,
    # because dateadd() works with second-level offsets (n * 86400).
    ("月", "months"),
    ("年", "years"),
]


class _DateInputContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self.setupUi()

    def setupUi(
        self
    ):

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self._modeCombo = QComboBox(self)
        self._modeCombo.addItem("相对日期", "relative")
        self._modeCombo.addItem("绝对日期", "absolute")
        self._modeCombo.setFixedHeight(25)
        self._stack = QStackedWidget(self)
        self._relCombo = QComboBox(self)
        for display, data in DATE_OPTIONS:
            self._relCombo.addItem(display, data)
        self._relCombo.setFixedHeight(25)
        self._stack.addWidget(self._relCombo)
        self._dateEdit = QDateEdit(self)
        self._dateEdit.setDisplayFormat("yyyy-MM-dd")
        self._dateEdit.setCalendarPopup(True)
        self._dateEdit.setFixedHeight(25)
        self._stack.addWidget(self._dateEdit)
        self._modeCombo.currentIndexChanged.connect(
            lambda i: self._stack.setCurrentIndex(i)
        )
        layout.addWidget(self._modeCombo)
        layout.addWidget(self._stack)
        layout.addStretch()

    def getValue(
        self
    ) -> str:

        mode = self._modeCombo.currentData()
        if mode == "relative":
            return self._relCombo.currentText()
        return self._dateEdit.date().toString("yyyy-MM-dd")


class _TimeInputContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._timeEdit = QTimeEdit(self)
        self._timeEdit.setDisplayFormat("HH:mm")
        self._timeEdit.setFixedHeight(25)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._timeEdit)

    def getValue(
        self
    ) -> str:

        return self._timeEdit.time().toString("HH:mm")


class _DateOffsetContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._spinBox = QSpinBox(self)
        self._spinBox.setRange(0, 99999)
        self._spinBox.setFixedHeight(25)
        self._unitCombo = QComboBox(self)
        for display, data in DATE_OFFSET_OPTIONS:
            self._unitCombo.addItem(display, data)
        self._unitCombo.setFixedHeight(25)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._spinBox)
        layout.addWidget(self._unitCombo)
        layout.addStretch()

    def getValue(
        self
    ) -> str:

        return str(self.getOffsetDays())

    def getOffsetDays(
        self
    ) -> int:

        val = self._spinBox.value()
        unit = self._unitCombo.currentData()
        if unit == "weeks":
            return val*7
        if unit == "months":
            return val*30
        if unit == "years":
            return val*365
        return val


class _TimeOffsetContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._spinBox = QSpinBox(self)
        self._spinBox.setRange(0, 99999)
        self._spinBox.setSuffix(" 小时")
        self._spinBox.setFixedHeight(25)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._spinBox)

    def getValue(
        self
    ) -> str:

        return str(self.getOffsetHours())

    def getOffsetHours(
        self
    ) -> int:

        return self._spinBox.value()


class VariableManager(QObject):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._vars = []
        self._nameMap = {}

        self.initPresetVars()

    def initPresetVars(
        self
    ):

        for p in getPresetVars():
            entry = {"name": p["name"], "type": p["type"], "display": p["display"]}
            self._vars.append(entry)
            self._nameMap[p["name"]] = entry

    def getInfoByName(
        self,
        name: str
    ):

        return self._nameMap.get(name.upper().strip())

    def populateCombo(
        self,
        combo: QComboBox
    ):

        currentData = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for entry in self._vars:
            combo.addItem(
                entry["display"],
                (entry["name"], entry["type"])
            )
        if currentData:
            for i in range(combo.count()):
                d = combo.itemData(i)
                if d and d[0] == currentData[0]:
                    combo.setCurrentIndex(i)
                    break
        combo.blockSignals(False)


def makeValueWidget(
    var_type: str,
    parent: QWidget = None
) -> QWidget:

    if var_type == "Int":
        w = QSpinBox(parent)
        w.setRange(-999999, 999999)
        w.setFixedHeight(25)
        w.setMinimumWidth(100)
        return w
    if var_type == "Float":
        w = QDoubleSpinBox(parent)
        w.setRange(-999999.0, 999999.0)
        w.setDecimals(2)
        w.setFixedHeight(25)
        w.setMinimumWidth(100)
        return w
    if var_type == "String":
        w = QLineEdit(parent)
        w.setPlaceholderText("输入值")
        w.setFixedHeight(25)
        w.setMinimumWidth(120)
        return w
    if var_type == "Boolean":
        w = QComboBox(parent)
        w.addItem("是 (true)", "true")
        w.addItem("否 (false)", "false")
        w.setFixedHeight(25)
        w.setMinimumWidth(100)
        return w
    if var_type == "Date":
        return _DateInputContainer(parent)
    if var_type == "Time":
        return _TimeInputContainer(parent)
    w = QLineEdit(parent)
    w.setPlaceholderText("输入值")
    w.setFixedHeight(25)
    w.setMinimumWidth(120)
    return w

def makeOffsetWidget(
    var_type: str,
    parent: QWidget = None
) -> QWidget:

    if var_type == "Int":
        w = QSpinBox(parent)
        w.setRange(-999999, 999999)
        w.setFixedHeight(25)
        w.setMinimumWidth(100)
        return w
    if var_type == "Float":
        w = QDoubleSpinBox(parent)
        w.setRange(-999999.0, 999999.0)
        w.setDecimals(2)
        w.setFixedHeight(25)
        w.setMinimumWidth(100)
        return w
    if var_type == "Date":
        return _DateOffsetContainer(parent)
    if var_type == "Time":
        return _TimeOffsetContainer(parent)
    w = QLabel("(不支持该操作)", parent)
    w.setFixedHeight(25)
    return w

def makeVarRefCombo(
    parent: QWidget = None
) -> QComboBox:

    cb = QComboBox(parent)
    cb.setFixedHeight(25)
    cb.setMinimumWidth(120)
    cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return cb

def makeComboWidget(
    items,
    min_width: int = 80,
    parent: QWidget = None
) -> QComboBox:

    cb = QComboBox(parent)
    for display, data in items:
        cb.addItem(display, data)
    cb.setFixedHeight(25)
    cb.setMinimumWidth(min_width)
    return cb

def makeLabel(
    text: str,
    parent: QWidget = None,
    width: int = None
) -> QLabel:

    lbl = QLabel(text, parent)
    lbl.setFixedHeight(25)
    if width:
        lbl.setFixedWidth(width)
    return lbl

def getValueFromWidget(
    w: QWidget
) -> str:

    if hasattr(w, "getValue"):
        return w.getValue()
    if isinstance(w, QTimeEdit):
        return w.time().toString("HH:mm")
    if isinstance(w, QDateEdit):
        return w.date().toString("yyyy-MM-dd")
    if isinstance(w, QComboBox):
        return w.currentData() or w.currentText()
    if isinstance(w, QSpinBox):
        return str(w.value())
    if isinstance(w, QDoubleSpinBox):
        return str(w.value())
    if isinstance(w, QLineEdit):
        return w.text()
    return ""

def encodeValueStr(
    raw_value: str,
    var_type: str
) -> str:
    """
        Encode a raw widget value as a Lua expression.

        Arithmetic expressions (A + B) are passed through for numeric types;
        Date/Time arithmetic is translated to ``dateadd()`` / ``timeadd()`` calls.
    """

    if var_type in ("Date", "Time"):
        return encodeDateOrTime(str(raw_value), var_type)
    if isinstance(raw_value, bool):
        return "true" if raw_value else "false"
    s = str(raw_value)
    if isArithExpr(s):
        return s
    if var_type == "Boolean":
        up = s.upper().strip()
        if up in ("TRUE", "FALSE"):
            return up.lower()
        return "true" if raw_value else "false"
    if var_type == "String":
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s

def encodeDateOrTime(
    raw_value: str,
    var_type: str
) -> str:
    """
        Translate a date/time widget value into a Lua expression.
    """

    s = raw_value.strip()
    up = s.upper()
    # Input comes from widget values — single binary expressions only (e.g. "A + 3",
    # "CURRENT_DATE + 5"). Multi-operator expressions are not produced by the UI.
    m_arith_spaced = re.match(r'^(.+?)\s+([+-])\s+(.+)$', s)
    m_arith_nospace = re.match(r'^([A-Za-z_]\w*)([+-])(\d+|[A-Za-z_]\w*)$', s)
    m_arith = m_arith_spaced or m_arith_nospace
    if m_arith:
        left = m_arith.group(1).strip().upper()
        sign = m_arith.group(2)
        right = m_arith.group(3).strip()
        operand = right if sign == "+" else f"-{right}"
        if left == "CURRENT_DATE":
            return f"dateadd(datenow(), {operand})"
        if left == "CURRENT_TIME":
            return f"timeadd(timenow(), {operand})"
        if var_type == "Date":
            return f"dateadd({left}, {operand})"
        if var_type == "Time":
            return f"timeadd({left}, {operand})"
        return f"{left} {sign} {right}"
    if up == "CURRENT_DATE":
        return "datenow()"
    if up == "CURRENT_TIME":
        return "timenow()"
    _REL_MAP = {
        "前天": "dateadd(datenow(), -2)",
        "昨天": "dateadd(datenow(), -1)",
        "今天": "datenow()",
        "明天": "dateadd(datenow(), 1)",
        "后天": "dateadd(datenow(), 2)",
    }
    if s in _REL_MAP:
        return _REL_MAP[s]
    if var_type == "Date":
        m_date = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
        if m_date:
            y, m, d = int(m_date.group(1)), int(m_date.group(2)), int(m_date.group(3))
            return f"date({y}, {m}, {d})"
    if var_type == "Time":
        m_time = re.match(r"^(\d{1,2}):(\d{2})$", s)
        if m_time:
            h, m = int(m_time.group(1)), int(m_time.group(2))
            return f"time({h}, {m})"
    if re.match(r"^[+-]?\d+$", s):
        return s
    if re.match(r"^[A-Za-z_]\w*$", s):
        return s
    return f'"{s}"'

# Pre-compiled patterns for detecting arithmetic expressions (A + B / A - B)
_RE_ARITH_SPACED = re.compile(r'^(.+?)\s+([+-])\s+(.+)$')
_RE_ARITH_NOSPACE = re.compile(r'^([A-Za-z_]\w*)([+-])(\d+|[A-Za-z_]\w*)$')

def isArithExpr(
    expr: str
) -> bool:
    """
        Return True if expr looks like a two-operand arithmetic expression (A ± B).
    """

    s = expr.strip()
    return bool(_RE_ARITH_SPACED.match(s) or _RE_ARITH_NOSPACE.match(s))
