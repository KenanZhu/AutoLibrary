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
    var_type: str
) -> bool:

    for t, a in VARTYPE_INFOS:
        if t == var_type:
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
        self.ModeCombo = QComboBox(self)
        self.ModeCombo.addItem("相对日期", "relative")
        self.ModeCombo.addItem("绝对日期", "absolute")
        self.ModeCombo.setFixedHeight(25)
        self.Stack = QStackedWidget(self)
        self.RelCombo = QComboBox(self)
        for display, data in DATE_OPTIONS:
            self.RelCombo.addItem(display, data)
        self.RelCombo.setFixedHeight(25)
        self.Stack.addWidget(self.RelCombo)
        self.DateEdit = QDateEdit(self)
        self.DateEdit.setDisplayFormat("yyyy-MM-dd")
        self.DateEdit.setCalendarPopup(True)
        self.DateEdit.setFixedHeight(25)
        self.Stack.addWidget(self.DateEdit)
        self.ModeCombo.currentIndexChanged.connect(
            lambda i: self.Stack.setCurrentIndex(i)
        )
        Layout.addWidget(self.ModeCombo)
        Layout.addWidget(self.Stack)
        Layout.addStretch()

    def getValue(
        self
    ) -> str:

        mode = self.ModeCombo.currentData()
        if mode == "relative":
            return self.RelCombo.currentText()
        return self.DateEdit.date().toString("yyyy-MM-dd")


class _TimeInputContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self.TimeEdit = QTimeEdit(self)
        self.TimeEdit.setDisplayFormat("HH:mm")
        self.TimeEdit.setFixedHeight(25)

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self.TimeEdit)

    def getValue(
        self
    ) -> str:

        return self.TimeEdit.time().toString("HH:mm")


class _DateOffsetContainer(QWidget):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self.SpinBox = QSpinBox(self)
        self.SpinBox.setRange(0, 99999)
        self.SpinBox.setFixedHeight(25)
        self.UnitCombo = QComboBox(self)
        for display, data in DATE_OFFSET_OPTIONS:
            self.UnitCombo.addItem(display, data)
        self.UnitCombo.setFixedHeight(25)

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(4)
        Layout.addWidget(self.SpinBox)
        Layout.addWidget(self.UnitCombo)
        Layout.addStretch()

    def getValue(
        self
    ) -> str:

        return str(self.getOffsetDays())

    def getOffsetDays(
        self
    ) -> int:

        val = self.SpinBox.value()
        unit = self.UnitCombo.currentData()
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
        self.SpinBox = QSpinBox(self)
        self.SpinBox.setRange(0, 99999)
        self.SpinBox.setSuffix(" 小时")
        self.SpinBox.setFixedHeight(25)

        Layout = QHBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self.SpinBox)

    def getValue(
        self
    ) -> str:

        return str(self.getOffsetHours())

    def getOffsetHours(
        self
    ) -> int:

        return self.SpinBox.value()


class VariableManager(QObject):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._vars = []
        self._name_map = {}

        self.initPresetVars()

    def initPresetVars(
        self
    ):

        for p in getPresetVars():
            entry = {"name": p["name"], "type": p["type"], "display": p["display"]}
            self._vars.append(entry)
            self._name_map[p["name"]] = entry

    def getInfoByName(
        self,
        name: str
    ):

        return self._name_map.get(name.upper().strip())

    def populateCombo(
        self,
        combo: QComboBox
    ):

        current_data = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        for entry in self._vars:
            combo.addItem(
                entry["display"],
                (entry["name"], entry["type"])
            )
        if current_data:
            for i in range(combo.count()):
                d = combo.itemData(i)
                if d and d[0] == current_data[0]:
                    combo.setCurrentIndex(i)
                    break
        combo.blockSignals(False)


def makeValueWidget(
    var_type: str,
    parent: QWidget = None
) -> QWidget:

    if var_type == "Int":
        Widget = QSpinBox(parent)
        Widget.setRange(-999999, 999999)
        Widget.setFixedHeight(25)
        Widget.setMinimumWidth(100)
        return Widget
    if var_type == "Float":
        Widget = QDoubleSpinBox(parent)
        Widget.setRange(-999999.0, 999999.0)
        Widget.setDecimals(2)
        Widget.setFixedHeight(25)
        Widget.setMinimumWidth(100)
        return Widget
    if var_type == "String":
        Widget = QLineEdit(parent)
        Widget.setPlaceholderText("输入值")
        Widget.setFixedHeight(25)
        Widget.setMinimumWidth(120)
        return Widget
    if var_type == "Boolean":
        Widget = QComboBox(parent)
        Widget.addItem("是 (true)", "true")
        Widget.addItem("否 (false)", "false")
        Widget.setFixedHeight(25)
        Widget.setMinimumWidth(100)
        return Widget
    if var_type == "Date":
        return _DateInputContainer(parent)
    if var_type == "Time":
        return _TimeInputContainer(parent)
    Widget = QLineEdit(parent)
    Widget.setPlaceholderText("输入值")
    Widget.setFixedHeight(25)
    Widget.setMinimumWidth(120)
    return Widget

def makeOffsetWidget(
    var_type: str,
    parent: QWidget = None
) -> QWidget:

    if var_type == "Int":
        Widget = QSpinBox(parent)
        Widget.setRange(-999999, 999999)
        Widget.setFixedHeight(25)
        Widget.setMinimumWidth(100)
        return Widget
    if var_type == "Float":
        Widget = QDoubleSpinBox(parent)
        Widget.setRange(-999999.0, 999999.0)
        Widget.setDecimals(2)
        Widget.setFixedHeight(25)
        Widget.setMinimumWidth(100)
        return Widget
    if var_type == "Date":
        return _DateOffsetContainer(parent)
    if var_type == "Time":
        return _TimeOffsetContainer(parent)
    Widget = QLabel("(不支持该操作)", parent)
    Widget.setFixedHeight(25)
    return Widget

def makeVarRefCombo(
    parent: QWidget = None
) -> QComboBox:

    ComboBox = QComboBox(parent)
    ComboBox.setFixedHeight(25)
    ComboBox.setMinimumWidth(120)
    ComboBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    return ComboBox

def makeComboWidget(
    items,
    min_width: int = 80,
    parent: QWidget = None
) -> QComboBox:

    ComboBox = QComboBox(parent)
    for display, data in items:
        ComboBox.addItem(display, data)
    ComboBox.setFixedHeight(25)
    ComboBox.setMinimumWidth(min_width)
    return ComboBox

def makeLabel(
    text: str,
    parent: QWidget = None,
    width: int = None
) -> QLabel:

    Label = QLabel(text, parent)
    Label.setFixedHeight(25)
    if width:
        Label.setFixedWidth(width)
    return Label

def getValueFromWidget(
    widget: QWidget
) -> str:

    if hasattr(widget, "getValue"):
        return widget.getValue()
    if isinstance(widget, QTimeEdit):
        return widget.time().toString("HH:mm")
    if isinstance(widget, QDateEdit):
        return widget.date().toString("yyyy-MM-dd")
    if isinstance(widget, QComboBox):
        return widget.currentData() or widget.currentText()
    if isinstance(widget, QSpinBox):
        return str(widget.value())
    if isinstance(widget, QDoubleSpinBox):
        return str(widget.value())
    if isinstance(widget, QLineEdit):
        return widget.text()
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
