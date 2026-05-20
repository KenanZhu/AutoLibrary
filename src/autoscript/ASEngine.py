# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import re
from datetime import (
    datetime,
    timedelta,
    date,
    time
)

from .ASObject import (
    ASObject,
    _META_VARS,
    _inferType
)
from .ASOperator import ASOperator
from .ASTokenizer import (
    ASTokenizer,
    NodeVisitor,
    Script,
    IfNode,
    SetNode,
    OpNode,
    PassNode,
    UnrecogNode
)


__all__ = ["execute", "addTargetVar", "splitTopLevel"]


# Engine state
# User-registered target variables (bound to target_data paths)
_TARGET_VARS = {}
# Free-form script variables (not bound to target_data)
_SCRIPT_VARS = {}
# Name -> ASObject lookup map built from _META_VARS, _TARGET_VARS, and display names
_FIELD_MAP = {}


def _errPos(
    line: int,
    message: str
) -> str:
    """
        Format an error message with a script line number.

        Args:
            line (int): The script line number where the error occurred.
            message (str): The error description.

        Returns:
            str: A formatted error string like "AutoScript syntax error(line X): message".
    """
    return f"AutoScript 语法错误(第{line}行): {message}"


# Pre-compiled regex patterns for value resolution
_RE_TIME = re.compile(r"^TIME\((\d{1,2}):(\d{2})\)$", re.IGNORECASE)
_RE_DATE = re.compile(r"^DATE\((\d{4})-(\d{2})-(\d{2})\)$", re.IGNORECASE)


def splitTopLevel(
    text: str,
    delimiter: str
) -> list:
    """
        Split a condition expression by a delimiter (.AND. / .OR.), respecting parentheses.

        Only splits at the top nesting level; delimiters inside parentheses are ignored.

        Args:
            text (str): The condition expression to split.
            delimiter (str): The delimiter string, e.g. ".OR." or ".AND.".

        Returns:
            list: A list of sub-expression strings (stripped of leading/trailing whitespace).
    """

    parts = []
    depth = 0
    buf = ""
    i = 0
    text_upper = text.upper()
    delim_upper = delimiter.upper()
    dlen = len(delim_upper)
    while i < len(text):
        if text[i] == "(":
            depth += 1
            buf += text[i]
        elif text[i] == ")":
            depth -= 1
            buf += text[i]
        elif depth == 0 and text_upper[i:i + dlen] == delim_upper:
            parts.append(buf)
            buf = ""
            i += dlen
            continue
        else:
            buf += text[i]
        i += 1
    if buf.strip():
        parts.append(buf)
    return parts


def _buildFieldMap():
    """
        Rebuild the _FIELD_MAP lookup from _META_VARS and _TARGET_VARS.

        Each variable is registered under both its canonical name (uppercased)
        and its display_name (if present), so that scripts can refer to either.
    """

    _FIELD_MAP.clear()
    for ch_name, obj in _META_VARS.items():
        _FIELD_MAP[obj.name.upper()] = obj
        _FIELD_MAP[ch_name.upper().strip()] = obj
    for obj in _TARGET_VARS.values():
        _FIELD_MAP[obj.name.upper()] = obj
        if obj.display_name:
            _FIELD_MAP[obj.display_name.upper().strip()] = obj


def _resolveFieldObj(
    field_name: str
):
    """
        Resolve a field name to its ASObject by looking up _FIELD_MAP then _SCRIPT_VARS.

        Unlike getting a raw value, this returns the ASObject instance itself,
        preserving type information for operations and comparisons.

        Args:
            field_name (str): The field name (case-insensitive).

        Returns:
            ASObject or None: The resolved ASObject, or None if not found.
    """

    upper_name = field_name.upper().strip()
    obj = _FIELD_MAP.get(upper_name)
    if obj:
        return obj
    obj = _SCRIPT_VARS.get(upper_name)
    if obj:
        return obj
    return None


def _resolveValue(
    value_str: str,
    target_data: dict
):
    """
        Parse and resolve a value string from a script into a Python object.

        Supports the following literal forms:
          - TIME(hh:mm)
          - DATE(yyyy-mm-dd)
          - .TRUE. / .FALSE.
          - Single/double quoted strings (with escaped single quotes)
          - Arithmetic expressions: operand (+|-) operand (Date ± Int, Int ± Int, etc.)
          - Numeric literals (int / float)
          - Field references (resolved via _resolveFieldObj)

        Args:
            value_str (str): The raw value string from the script.
            target_data (dict): The application data dict.

        Returns:
            The resolved Python value.
    """

    s = value_str.strip()
    m = _RE_TIME.match(s)
    if m:
        return time(int(m.group(1)), int(m.group(2)))
    m = _RE_DATE.match(s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    up = s.upper()
    if up == ".TRUE.":
        return True
    if up == ".FALSE.":
        return False
    if s.startswith("'") and s.endswith("'"):
        return s[1:-1].replace("''", "'")
    if s.startswith('"') and s.endswith('"'):
        return s[1:-1]
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
    arith_result = _resolveArithExpr(s, target_data)
    if arith_result is not None:
        return arith_result
    obj = _resolveFieldObj(s)
    if obj:
        return obj.getValue(target_data)
    return ""


def _resolveAsObject(
    expr: str,
    target_data: dict
) -> ASObject:
    """
        Resolve a value expression to an ASObject.

        - If the expression is a registered field name, returns its ASObject directly.
        - If the expression is a literal (number, string, DATE(), TIME(), bool),
          creates a temporary ASObject with the inferred type.

        This is the key function that ensures all internal operations work
        with typed ASObject instances rather than raw Python values.

        Args:
            expr (str): The raw expression string from the script.
            target_data (dict): The application data dict.

        Returns:
            ASObject: A registered or temporary ASObject representing the expression value.
    """

    s = expr.strip()
    obj = _resolveFieldObj(s)
    if obj is not None:
        return obj
    value = _resolveValue(s, target_data)
    inferred = _inferType(value, s)
    return ASObject._makeTemp(value, inferred)


def _resolveArithExpr(
    expr: str,
    target_data: dict,
    line: int = 0
):
    """
        Try to evaluate expr as a two-operand arithmetic expression: left (+|-) right.

        Each operand is resolved via _resolveAsObject, reusing the full literal /
        field / script-variable resolution stack.  The left operand's value is
        copied into a temporary ASObject and ASOperator.apply() performs the
        type-safe calculation on the copy, so the original variable is never
        mutated.

        Returns the computed Python value, or None if expr is not a recognised
        arithmetic pattern.
    """

    s = expr.strip()
    m = re.match(r'^(.+?)\s+([+-])\s+(.+)$', s)
    if not m:
        # Fallback for no-space expressions like RESERVE_DATE+1
        # (e.g. when extracted from IF(RESERVE_DATE.EQ.CURRENT_DATE+1)).
        # Left operand must be an identifier (letter/underscore start) to
        # avoid false-matching date strings like 2026-05-20.
        m = re.match(r'^([A-Za-z_]\w*)([+-])(\d+|[A-Za-z_]\w*)$', s)
    if not m:
        return None
    left_expr = m.group(1).strip()
    op_symbol = m.group(2).strip()
    right_expr = m.group(3).strip()
    if " + " in left_expr or " - " in left_expr:
        return None
    if " + " in right_expr or " - " in right_expr:
        return None
    left_obj = _resolveAsObject(left_expr, target_data)
    right_obj = _resolveAsObject(right_expr, target_data)
    op = ".ADD." if op_symbol == "+" else ".SUB."
    left_val = left_obj.getValue(target_data)
    result_type = left_obj.var_type
    if left_obj.var_type == "Int" and right_obj.var_type == "Float":
        result_type = "Float"
    elif left_obj.var_type == "Float" and right_obj.var_type == "Int":
        result_type = "Float"
    temp = ASObject._makeTemp(left_val, result_type)
    ASOperator.apply(temp, right_obj, op, target_data)
    return temp.getValue(target_data)


def _evaluateCondition(
    condition_str: str,
    target_data: dict,
    line: int = 0
) -> bool:
    """
        Evaluate a condition expression and return a boolean result.

        Supports:
          - Boolean literals: .TRUE., .FALSE.
          - .AND. / .OR. operators (lowest precedence)
          - Parenthesised sub-expressions
          - Comparison operators: .EQ., .NEQ., .BGT., .BLT., .BGE., .BLE.

        All operands are resolved as ASObject instances (via _resolveAsObject)
        and comparisons are delegated to ASOperator.compare().

        Args:
            condition_str (str): The raw condition expression from the script.
            target_data (dict): The application data dict.

        Returns:
            bool: The evaluation result.

        Raises:
            ValueError: If the expression contains unrecognised tokens or type-mismatched comparisons.
    """

    s = condition_str.strip()
    if not s:
        return False
    or_parts = splitTopLevel(s, ".OR.")
    if len(or_parts) > 1:
        return any(
            _evaluateCondition(p.strip(), target_data, line)
            for p in or_parts
        )
    and_parts = splitTopLevel(s, ".AND.")
    if len(and_parts) > 1:
        return all(
            _evaluateCondition(p.strip(), target_data, line)
            for p in and_parts
        )
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        return _evaluateCondition(s[1:-1], target_data, line)
    up = s.upper()
    if up == ".TRUE.":
        return True
    if up == ".FALSE.":
        return False
    for op in ASOperator._COMPARE:
        idx = up.find(op.upper())
        if idx < 0:
            continue
        left_raw = s[:idx].strip()
        right_raw = s[idx + len(op):].strip()
        try:
            left_obj = _resolveAsObject(left_raw, target_data)
            right_obj = _resolveAsObject(right_raw, target_data)
            return ASOperator.compare(left_obj, right_obj, op, target_data)
        except ValueError as e:
            raise ValueError(_errPos(line, str(e)))
    raise ValueError(
        _errPos(line, f"无法识别的条件表达式 '{condition_str}'")
    )


def _executeSet(
    line_text: str,
    target_data: dict,
    line: int = 0
):
    """
        Execute a SET statement to assign a value to a field or script variable.

        Parses the line as "SET field_name = value_expr", resolves the value,
        and assigns it. If the target field does not exist, a new script variable
        is created with an inferred type.

        Args:
            line (str): The raw SET line from the script.
            target_data (dict): The application data dict.

        Raises:
            ValueError: If the value string contains unexpected extra tokens.
    """

    rest = line_text[3:].strip()
    eq_idx = rest.find("=")
    if eq_idx < 0:
        return
    field_name = rest[:eq_idx].strip()
    value_str = rest[eq_idx + 1:].strip()
    if not field_name:
        return
    resolved = _resolveValue(value_str, target_data)
    stripped = value_str.strip()
    if resolved == "" and stripped not in ("''", '""') and len(stripped.split()) > 1:
        try:
            resolved = _resolveArithExpr(stripped, target_data, line)
        except ValueError as e:
            raise ValueError(_errPos(line, str(e)))
        if resolved is None:
            raise ValueError(_errPos(line, f"SET 值中存在多余内容 '{stripped}'"))
    upper_name = field_name.upper().strip()
    obj = _FIELD_MAP.get(upper_name)
    if not obj:
        obj = _SCRIPT_VARS.get(upper_name)
    if obj:
        try:
            obj.setValue(resolved, target_data)
        except ValueError as e:
            raise ValueError(_errPos(line, str(e)))
        return
    inferred_type = _inferType(resolved, stripped)
    new_var = ASObject(
        upper_name,
        inferred_type,
        read_only=False,
        is_config=False,
        default_value=resolved
    )
    _SCRIPT_VARS[upper_name] = new_var


def _executeOperation(
    line_text: str,
    target_data: dict,
    line: int = 0
):
    """
        Execute a field operation statement: "FIELD .ADD. N" or "FIELD .SUB. N".

        Resolves the left side as a registered ASObject and the right side
        as a temporary numeric ASObject, then delegates to ASOperator.apply().

        Args:
            line (str): The raw operation line from the script (e.g. "RESERVE_DATE .ADD. 1").
            target_data (dict): The application data dict.

        Raises:
            ValueError: If the field is unknown, the operand is invalid,
                        or the type does not support the operation.
    """

    parts = line_text.split()
    if len(parts) < 3:
        return
    if len(parts) > 3:
        raise ValueError(
            _errPos(line, f"操作语句中存在多余内容 '{' '.join(parts[3:])}'")
        )
    field_name = parts[0].upper().strip()
    op = parts[1].upper().strip()
    raw_value = parts[2].strip()
    target = _resolveFieldObj(field_name)
    if target is None:
        raise ValueError(_errPos(line, f"未知字段 '{field_name}'"))
    try:
        operand = _resolveAsObject(raw_value, target_data)
        ASOperator.apply(target, operand, op, target_data)
    except ValueError as e:
        raise ValueError(_errPos(line, str(e)))


def addTargetVar(
    name: str,
    var_type: str,
    key_path: list,
    display_name: str = None
):
    """
        Register a new target variable bound to a path in the application data dict.

        Once registered, the variable can be read, written, and operated on in scripts
        using its canonical name or display_name.

        Args:
            name (str): The canonical variable name (e.g. "RESERVE_DATE").
            var_type (str): The type ("Int", "Float", "Boolean", "Date", "Time", "String").
            key_path (list): The nested path into target_data, e.g. ["reserve_info", "date"].
            display_name (str): An optional Chinese alias for use in script conditions.

        Example:
            >>> addTargetVar("MY_FIELD", "String", ["custom", "field"], display_name="自定义字段")
    """

    upper_name = name.upper().strip()
    obj = ASObject(
        upper_name,
        var_type,
        is_config=True,
        key_path=key_path,
        display_name=display_name
    )
    _TARGET_VARS[upper_name] = obj


class _EngineExecutor(NodeVisitor):
    """
        AST visitor that executes AutoScript against target_data.
        Walks the AST and dispatches SET / ADD / SUB operations
        via visitScript / visitIf / visitSet / visitOp / visitPass / visitUnrecog.
    """

    def __init__(
        self,
        target_data: dict
    ):

        super().__init__()
        self._target_data = target_data
        self._cur_line = 0

    @property
    def _line(self) -> int:
        """Return current line number for _errPos calls."""

        return self._cur_line


    def _incLine(
        self
    ):

        self._cur_line += 1


    def visitScript(
        self,
        _node: Script
    ):

        for child in _node.body:
            child.accept(self)


    def visitIf(
        self,
        _node: IfNode
    ):

        self._incLine()
        if not _node.closed:
            raise ValueError(_errPos(self._line, "IF 与 ENDIF / END IF 不匹配"))
        matched = _evaluateCondition(_node.condition, self._target_data, self._line)
        if matched:
            for child in _node.body:
                child.accept(self)
        else:
            executed = False
            for elif_node in _node.elif_branches:
                self._incLine()
                if _evaluateCondition(elif_node.condition, self._target_data, self._line):
                    for child in elif_node.body:
                        child.accept(self)
                    executed = True
                    break
            if not executed and _node.else_body:
                self._incLine()
                for child in _node.else_body:
                    child.accept(self)


    def visitSet(
        self,
        _node: SetNode
    ):

        self._incLine()
        full_line = f"SET {_node.target} = {_node.value}"
        _executeSet(full_line, self._target_data, self._line)


    def visitOp(
        self,
        _node: OpNode
    ):

        self._incLine()
        op_upper = _node.op_type.upper()
        full_line = f"{_node.target} .{op_upper}. {_node.value}"
        _executeOperation(full_line, self._target_data, self._line)


    def visitPass(
        self,
        _node: PassNode
    ):

        self._incLine()


    def visitUnrecog(
        self,
        _node: UnrecogNode
    ):

        self._incLine()
        upper = _node.raw_line.upper().strip()
        if upper.startswith("IF"):
            paren_open = upper.find("(")
            if paren_open < 0:
                raise ValueError(_errPos(self._line, "IF 缺少左括号"))
            depth = 1
            for ci in range(paren_open + 1, len(upper)):
                if upper[ci] == "(":
                    depth += 1
                elif upper[ci] == ")":
                    depth -= 1
                    if depth == 0:
                        remaining = upper[ci + 1:].strip()
                        if remaining and remaining != "THEN":
                            raise ValueError(_errPos(self._line, f"IF 条件后存在多余内容 '{remaining}'"))
                        break
            if depth > 0:
                raise ValueError(_errPos(self._line, "IF 缺少右括号"))
        elif upper.startswith("ELSE IF"):
            paren_open = upper.find("(")
            if paren_open < 0:
                raise ValueError(_errPos(self._line, "ELSE IF 缺少左括号"))
        raise ValueError(_errPos(self._line, f"无法识别的语法 '{_node.raw_line}'"))


def execute(
    script_text: str,
    target_data: dict
):
    """
        Execute an AutoScript on the given target data.

        Parses the script into an AST via ASTokenizer.parse(),
        then walks the tree with a visitor to evaluate conditions
        and dispatch SET / ADD / SUB operations.

        Args:
            script_text (str): The AutoScript source code.
            target_data (dict): The application data dict to read from / write to.

        Raises:
            ValueError: On syntax errors, unbalanced IF/END IF, unknown fields, etc.
    """

    _buildFieldMap()
    if not script_text or not script_text.strip():
        return
    ast = ASTokenizer.parse(script_text)
    if not ast.body:
        return
    executor = _EngineExecutor(target_data)
    ast.accept(executor)
