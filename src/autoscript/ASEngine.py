# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import re
from datetime import datetime, timedelta, date, time

from .ASObject import ASObject, _META_VARS, _inferType
from .ASOperator import ASOperator


__all__ = ["execute", "addTargetVar"]


# Engine state
# User-registered target variables (bound to target_data paths)
_TARGET_VARS = {}
# Free-form script variables (not bound to target_data)
_SCRIPT_VARS = {}
# Name -> ASObject lookup map built from _META_VARS, _TARGET_VARS, and display names
_FIELD_MAP = {}
# Current line number for error reporting
_CUR_LINE = 0


def _errPos(
    message: str
) -> str:
    """
        Format an error message with the current script line number.

        Args:
            message (str): The error description.

        Returns:
            str: A formatted error string like "AutoScript syntax error(line X): message".
    """
    return f"AutoScript 语法错误(第{_CUR_LINE}行): {message}"


def _findConditionBegin(
    upper_line: str
) -> int:
    """
        Find the position of the opening parenthesis that starts a condition.

        Args:
            upper_line (str): The uppercased IF / ELSE IF line.

        Returns:
            int: Index of '(' or -1 if not found.
    """
    return upper_line.find("(")


def _findConditionEnd(
    upper_line: str,
    start_pos: int
) -> int:
    """
        Find the matching closing parenthesis for a condition expression.

        Handles nested parentheses and optionally strips a trailing "THEN" keyword.

        Args:
            upper_line (str): The uppercased IF / ELSE IF line.
            start_pos (int): Index of the opening '('.

        Returns:
            int: Index of the matching ')' or -1 if unbalanced.
    """

    line = upper_line.rstrip()
    if line.endswith(" THEN"):
        line = line[:-5].rstrip()
    depth = 1
    for i in range(start_pos + 1, len(line)):
        ch = line[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    return -1


def _splitTopLevel(
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
          - CURRENT_DATE + N / CURRENT_TIME + N (relative offsets)
          - Numeric literals (int / float)
          - Field references (resolved via _resolveFieldObj)

        Args:
            value_str (str): The raw value string from the script.
            target_data (dict): The application data dict.

        Returns:
            The resolved Python value.
    """

    s = value_str.strip()
    m = re.match(r"^TIME\((\d{1,2}):(\d{2})\)$", s, re.IGNORECASE)
    if m:
        return time(int(m.group(1)), int(m.group(2)))
    m = re.match(r"^DATE\((\d{4})-(\d{2})-(\d{2})\)$", s, re.IGNORECASE)
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
    m = re.match(r"^CURRENT_DATE\s*\+\s*(\d+)$", s, re.IGNORECASE)
    if m:
        days = int(m.group(1))
        return datetime.now().date() + timedelta(days=days)
    m = re.match(r"^CURRENT_TIME\s*\+\s*(\d+)$", s, re.IGNORECASE)
    if m:
        hours = int(m.group(1))
        return (datetime.now() + timedelta(hours=hours)).time()
    try:
        return int(s)
    except ValueError:
        pass
    try:
        return float(s)
    except ValueError:
        pass
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


def _evaluateCondition(
    condition_str: str,
    target_data: dict
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
    or_parts = _splitTopLevel(s, ".OR.")
    if len(or_parts) > 1:
        return any(
            _evaluateCondition(p.strip(), target_data)
            for p in or_parts
        )
    and_parts = _splitTopLevel(s, ".AND.")
    if len(and_parts) > 1:
        return all(
            _evaluateCondition(p.strip(), target_data)
            for p in and_parts
        )
    s = s.strip()
    if s.startswith("(") and s.endswith(")"):
        return _evaluateCondition(s[1:-1], target_data)
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
        left_obj = _resolveAsObject(left_raw, target_data)
        right_obj = _resolveAsObject(right_raw, target_data)
        return ASOperator.compare(left_obj, right_obj, op, target_data)
    raise ValueError(
        _errPos(f"无法识别的条件表达式 '{condition_str}'")
    )


def _executeSet(
    line: str,
    target_data: dict
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

    rest = line[3:].strip()
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
        raise ValueError(_errPos(f"SET 值中存在多余内容 '{stripped}'"))
    upper_name = field_name.upper().strip()
    obj = _FIELD_MAP.get(upper_name)
    if not obj:
        obj = _SCRIPT_VARS.get(upper_name)
    if obj:
        obj.setValue(resolved, target_data)
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
    line: str,
    target_data: dict
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

    parts = line.split()
    if len(parts) < 3:
        return
    if len(parts) > 3:
        raise ValueError(
            _errPos(f"操作语句中存在多余内容 '{' '.join(parts[3:])}'")
        )
    field_name = parts[0].upper().strip()
    op = parts[1].upper().strip()
    raw_value = parts[2].strip()
    target = _resolveFieldObj(field_name)
    if target is None:
        raise ValueError(_errPos(f"未知字段 '{field_name}'"))
    operand = _resolveAsObject(raw_value, target_data)
    ASOperator.apply(target, operand, op, target_data)


def _assertInIf(
    if_stack: list,
    line: str
):
    """
        Assert that an executable statement is inside an IF block.

        Args:
            if_stack (list): The current IF nesting stack.
            line (str): The statement line (used for error message).

        Raises:
            ValueError: If if_stack is empty (statement is outside any IF block).
    """

    if not if_stack:
        raise ValueError(_errPos(f"可执行语句必须位于 IF 块内: {line}"))


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


def execute(
    script_text: str,
    target_data: dict
):
    """
        Execute an AutoScript on the given target data.

        Parses the script line by line, maintaining an IF nesting stack to control
        which blocks are active. Supports IF / ELSE IF / ELSE / END IF control flow,
        SET assignments, PASS no-ops, and .ADD. / .SUB. field operations.

        Args:
            script_text (str): The AutoScript source code.
            target_data (dict): The application data dict to read from / write to.

        Raises:
            ValueError: On syntax errors, unbalanced IF/END IF, unknown fields, etc.

        Example:
            >>> data = {"reserve_info": {"date": "2026-05-01"}}
            >>> execute(
            ...     "IF(.TRUE.)\\n"
            ...     "    RESERVE_DATE .ADD. 1\\n"
            ...     "END IF",
            ...     data
            ... )
            >>> data["reserve_info"]["date"]
            '2026-05-02'
    """

    global _CUR_LINE

    _buildFieldMap()
    if not script_text or not script_text.strip():
        return
    lines = [l.strip() for l in script_text.split("\n") if l.strip()]
    if not lines:
        return
    if_stack = []
    for _CUR_LINE, line in enumerate(lines, 1):
        upper_line = line.upper().strip()
        if upper_line.startswith("IF"):
            paren_open = _findConditionBegin(upper_line)
            if paren_open < 0:
                raise ValueError(_errPos("IF 缺少左括号"))
            cond_end = _findConditionEnd(upper_line, paren_open)
            if cond_end < 0:
                raise ValueError(_errPos("IF 缺少右括号"))
            remaining = upper_line[cond_end + 1:].strip()
            if remaining and remaining.upper() != "THEN":
                raise ValueError(_errPos(f"IF 条件后存在多余内容 '{remaining}'"))
            condition_str = line[paren_open + 1:cond_end].strip()
            matched = _evaluateCondition(condition_str, target_data)
            if_stack.append([matched, matched])
        elif upper_line.startswith("ELSE IF"):
            if not if_stack:
                raise ValueError(_errPos("ELSE IF 前缺少 IF"))
            paren_open = _findConditionBegin(upper_line)
            if paren_open < 0:
                raise ValueError(_errPos("ELSE IF 缺少左括号"))
            cond_end = _findConditionEnd(upper_line, paren_open)
            if cond_end < 0:
                raise ValueError(_errPos("ELSE IF 缺少右括号"))
            remaining = upper_line[cond_end + 1:].strip()
            if remaining and remaining.upper() != "THEN":
                raise ValueError(_errPos(f"ELSE IF 条件后存在多余内容 '{remaining}'"))
            _, branch_matched = if_stack[-1]
            if not branch_matched:
                condition_str = line[paren_open + 1:cond_end].strip()
                matched = _evaluateCondition(condition_str, target_data)
                if_stack[-1] = [matched, matched]
            else:
                if_stack[-1][0] = False
        elif upper_line == "ELSE":
            if not if_stack:
                raise ValueError(_errPos("ELSE 前缺少 IF"))
            _, branch_matched = if_stack[-1]
            if not branch_matched:
                if_stack[-1] = [True, True]
            else:
                if_stack[-1][0] = False
        elif upper_line in ("ENDIF", "END IF"):
            if not if_stack:
                raise ValueError(_errPos("ENDIF / END IF 前缺少 IF"))
            if_stack.pop()
        elif upper_line.startswith("SET "):
            _assertInIf(if_stack, line)
            if all(ctx[0] for ctx in if_stack):
                _executeSet(line, target_data)
        elif upper_line == "PASS":
            continue
        else:
            _assertInIf(if_stack, line)
            if all(ctx[0] for ctx in if_stack):
                _executeOperation(line, target_data)
    if if_stack:
        raise ValueError(
            "AutoScript 语法错误: IF 与 ENDIF / END IF 不匹配"
        )
