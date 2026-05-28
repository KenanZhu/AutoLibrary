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

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(4)
        self._ModeCombo = QComboBox(self)
        self._ModeCombo.addItem("相对日期", "relative")
        self._ModeCombo.addItem("绝对日期", "absolute")
        self._ModeCombo.setFixedHeight(25)
        self._Stack = QStackedWidget(self)
        self._RelCombo = QComboBox(self)
        for display, data in DATE_OPTIONS:
            self._RelCombo.addItem(display, data)
        self._RelCombo.setFixedHeight(25)
        self._Stack.addWidget(self._RelCombo)
        self._DateEdit = QDateEdit(self)
        self._DateEdit.setDisplayFormat("yyyy-MM-dd")
        self._DateEdit.setCalendarPopup(True)
        self._DateEdit.setFixedHeight(25)
        self._Stack.addWidget(self._DateEdit)
        self._ModeCombo.currentIndexChanged.connect(
            lambda i: self._Stack.setCurrentIndex(i)
        )
        Layout.addWidget(self._ModeCombo)
        Layout.addWidget(self._Stack)
        Layout.addStretch()

    def getValue(
        self
    ) -> str:

        mode = self._ModeCombo.currentData()
        if mode == "relative":
            return self._RelCombo.currentText()
        return self._DateEdit.date().toString("yyyy-MM-dd")


class _TimeInputContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._TimeEdit = QTimeEdit(self)
        self._TimeEdit.setDisplayFormat("HH:mm")
        self._TimeEdit.setFixedHeight(25)

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self._TimeEdit)

    def getValue(
        self
    ) -> str:

        return self._TimeEdit.time().toString("HH:mm")


class _DateOffsetContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._SpinBox = QSpinBox(self)
        self._SpinBox.setRange(0, 99999)
        self._SpinBox.setFixedHeight(25)
        self._UnitCombo = QComboBox(self)
        for display, data in DATE_OFFSET_OPTIONS:
            self._UnitCombo.addItem(display, data)
        self._UnitCombo.setFixedHeight(25)

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(4)
        Layout.addWidget(self._SpinBox)
        Layout.addWidget(self._UnitCombo)
        Layout.addStretch()

    def getValue(
        self
    ) -> str:

        return str(self.getOffsetDays())

    def getOffsetDays(
        self
    ) -> int:

        val = self._SpinBox.value()
        unit = self._UnitCombo.currentData()
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
        self._SpinBox = QSpinBox(self)
        self._SpinBox.setRange(0, 99999)
        self._SpinBox.setSuffix(" 小时")
        self._SpinBox.setFixedHeight(25)

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self._SpinBox)

    def getValue(
        self
    ) -> str:

        return str(self.getOffsetHours())

    def getOffsetHours(
        self
    ) -> int:

        return self._SpinBox.value()


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

    Cb = QComboBox(parent)
    Cb.setFixedHeight(25)
    Cb.setMinimumWidth(120)
    Cb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return Cb

def makeComboWidget(
    items,
    min_width: int = 80,
    parent: QWidget = None
) -> QComboBox:

    Cb = QComboBox(parent)
    for display, data in items:
        Cb.addItem(display, data)
    Cb.setFixedHeight(25)
    Cb.setMinimumWidth(min_width)
    return Cb

def makeLabel(
    text: str,
    parent: QWidget = None,
    width: int = None
) -> QLabel:

    Lbl = QLabel(text, parent)
    Lbl.setFixedHeight(25)
    if width:
        Lbl.setFixedWidth(width)
    return Lbl

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
