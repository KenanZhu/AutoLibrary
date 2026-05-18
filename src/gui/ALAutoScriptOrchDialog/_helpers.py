"""
Helper utilities and constants for the AutoScript orchestration dialog.
"""
import re

from PySide6.QtCore import (
    QObject,
    QDate,
    QTime
)
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

from autoscript import (
    ALL_VARIABLES,
    splitTopLevel
)
from autoscript.ASOperator import (
    ARITH_TYPES,
    COMPARISON_OPERATORS
)


VAR_TYPE_ORDER = [
    "String",
    "Int",
    "Float",
    "Boolean",
    "Date",
    "Time"
]
PRESET_VARIABLES = [
    {
        "name": name.upper(),
        "type": vtype,
        "display": display
    }
    for display, (name, vtype) in ALL_VARIABLES.items()
]
PRESET_NAMES = {
    p["name"] for p in PRESET_VARIABLES
}
# Operator display names (UI-specific), symbols derived from engine
_COMPARE_DISPLAY_MAP = {
    ".EQ.": "等于",
    ".NEQ.": "不等于",
    ".BGT.": "大于",
    ".BLT.": "小于",
    ".BGE.": "大于等于",
    ".BLE.": "小于等于",
}
COMPARE_OPERATORS = sorted(
    [(name, op) for op, name in _COMPARE_DISPLAY_MAP.items() if op in COMPARISON_OPERATORS],
    key=lambda x: len(x[1]), reverse=True
)
LOGIC_OPERATORS = [
    ("并且 (.AND.)", ".AND."),
    ("或者 (.OR.)", ".OR."),
]
ACTION_TYPES = [
    ("设置为", "set"),
    ("增加", "add"),
    ("减少", "sub"),
]
DATE_RELATIVE_OPTIONS = [
    ("前天", "day_before_yesterday"),
    ("昨天", "yesterday"),
    ("今天", "today"),
    ("明天", "tomorrow"),
    ("后天", "day_after_tomorrow")
]
DATE_OFFSET_UNITS = [
    ("天", "days"),
    ("周", "weeks"),
    ("月", "months"),
    ("年", "years"),
]


class VariableManager(QObject):

    def __init__(
        self,
        parent = None
    ):

        super().__init__(parent)
        self._vars = []
        self._nameMap = {}

        self._initPresetVars()


    def _initPresetVars(
        self
    ):

        for p in PRESET_VARIABLES:
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


    def findExactNameEntry(
        self,
        combo: QComboBox,
        name: str
    ) -> int:

        name = name.upper().strip()
        for i in range(combo.count()):
            d = combo.itemData(i)
            if d and len(d) >= 1 and d[0].upper().strip() == name:
                return i
        return -1


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
        w.addItem("是 (.TRUE.)", ".TRUE.")
        w.addItem("否 (.FALSE.)", ".FALSE.")
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
        for display, data in DATE_RELATIVE_OPTIONS:
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


    def setValue(
        self,
        expr: str
    ):

        s = expr.strip().upper()
        _RELATIVE_MAP = {
            "CURRENT_DATE": 2, "TODAY": 2,
            "CURRENT_DATE + 1": 3, "TOMORROW": 3,
            "CURRENT_DATE + 2": 4,
            "CURRENT_DATE - 1": 1,
            "CURRENT_DATE - 2": 0,
        }
        idx = _RELATIVE_MAP.get(s)
        if idx is not None:
            self._modeCombo.setCurrentIndex(0)
            self._relCombo.setCurrentIndex(idx)
        elif s.startswith("DATE("):
            self._modeCombo.setCurrentIndex(1)
            m = re.match(r"DATE\((\d{4}-\d{2}-\d{2})\)", s)
            if m:
                parts = m.group(1).split("-")
                self._dateEdit.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))


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


    def setValue(
        self,
        expr: str
    ):

        s = expr.strip().upper()
        m = re.match(r"TIME\((\d{1,2}:\d{2})\)", s)
        if m:
            parts = m.group(1).split(":")
            self._timeEdit.setTime(QTime(int(parts[0]), int(parts[1])))


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
        for display, data in DATE_OFFSET_UNITS:
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


    def setValue(
        self,
        expr: str
    ):

        s = expr.strip().lstrip("+")
        try:
            self._spinBox.setValue(int(s))
        except ValueError:
            pass


    def getOffsetDays(
        self
    ) -> int:

        val = self._spinBox.value()
        unit = self._unitCombo.currentData()
        if unit == "weeks":
            return val * 7
        if unit == "months":
            return val * 30
        if unit == "years":
            return val * 365
        return val


    def getRawValue(
        self
    ) -> str:

        return str(self._spinBox.value())


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


    def setValue(
        self,
        expr: str
    ):

        s = expr.strip().lstrip("+")
        try:
            self._spinBox.setValue(int(s))
        except ValueError:
            pass


    def getOffsetHours(
        self
    ) -> int:

        return self._spinBox.value()


    def getRawValue(
        self
    ) -> str:

        return str(self._spinBox.value())


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


def setWidgetValue(
    w: QWidget,
    var_type: str,
    expr: str
):

    if hasattr(w, "setValue"):
        w.setValue(expr)
        return
    s = expr.strip().upper()
    if isinstance(w, QTimeEdit):
        m = re.match(r"TIME\((\d{1,2}:\d{2})\)", s)
        if m:
            parts = m.group(1).split(":")
            w.setTime(QTime(int(parts[0]), int(parts[1])))
    elif isinstance(w, QDateEdit):
        m = re.match(r"DATE\((\d{4}-\d{2}-\d{2})\)", s)
        if m:
            parts = m.group(1).split("-")
            w.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
    elif isinstance(w, QComboBox):
        for i in range(w.count()):
            if w.itemData(i) == s or w.itemText(i).upper() == s:
                w.setCurrentIndex(i)
                return
    elif isinstance(w, QSpinBox):
        try:
            w.setValue(int(expr))
        except ValueError:
            pass
    elif isinstance(w, QDoubleSpinBox):
        try:
            w.setValue(float(expr))
        except ValueError:
            pass
    elif isinstance(w, QLineEdit):
        inner = expr.strip()
        if (inner.startswith("'") and inner.endswith("'")) or \
           (inner.startswith('"') and inner.endswith('"')):
            inner = inner[1:-1].replace("''", "'")
        w.setText(inner)


def encodeValueStr(
    raw_value: str,
    var_type: str
) -> str:

    if var_type == "Time":
        if raw_value.startswith("+") or raw_value.startswith("-"):
            return raw_value
        if raw_value.startswith("TIME_OFFSET"):
            m = re.match(r"TIME_OFFSET\(([+-]\d+),(\w+)\)", raw_value)
            if m:
                return m.group(1)
            return raw_value
        return f"TIME({raw_value})"
    if var_type == "Date":
        relMap = {
            "前天": "CURRENT_DATE - 2",
            "昨天": "CURRENT_DATE - 1",
            "今天": "CURRENT_DATE",
            "明天": "CURRENT_DATE + 1",
            "后天": "CURRENT_DATE + 2"
        }
        if raw_value in relMap:
            return relMap[raw_value]
        return f"DATE({raw_value})"
    if var_type == "Boolean":
        up = raw_value.upper().strip()
        if up in (".TRUE.", ".FALSE."):
            return up
        return ".TRUE." if raw_value else ".FALSE."
    if var_type == "String":
        escaped = raw_value.replace("'", "''")
        return f"'{escaped}'"
    return raw_value


def stripOuterParens(
    s: str
) -> str:

    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        depth = 0
        for i, ch in enumerate(s):
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0 and i < len(s) - 1:
                    return s
        return s[1:-1].strip()
    return s


def isVarReference(
    expr: str
) -> bool:

    s = expr.strip()
    up = s.upper()
    if up in (".TRUE.", ".FALSE."):
        return False
    if re.match(r"^TIME\(|^DATE\(|^CURRENT_", up):
        return False
    if up.startswith("'") or up.startswith('"'):
        return False
    if re.match(r"^[+-]?\d", s):
        return False
    return bool(re.match(r"^[A-Z_][A-Z0-9_]*$", up))


def findOperatorIn(
    text: str,
    operators: list
) -> tuple[int, str] | None:

    for op in operators:
        op_upper = op.upper()
        start = 0
        while True:
            idx = text.upper().find(op_upper, start)
            if idx < 0:
                break
            if _isInsideLiteral(text, idx):
                start = idx + 1
                continue
            return (idx, op)
    return None


def _isInsideLiteral(
    text: str,
    pos: int
) -> bool:

    in_single = False
    in_double = False
    for i, ch in enumerate(text):
        if i >= pos:
            break
        if ch == "'" and not in_double:
            in_single = not in_single
        elif ch == '"' and not in_single:
            in_double = not in_double
    return in_single or in_double
