# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import re
from datetime import datetime, timedelta


class AutoScriptEngine:
    """
        AutoScript script engine.

        Parses and executes AutoScript — a lightweight scripting DSL
        used in repeatable timer tasks to preprocess user reservation
        data before automation runs.

        Supports IF/ELSE IF/ELSE/END IF control flow, SET assignments,
        .ADD./.SUB. operations on Date/Time fields, and rich comparison
        operators (.EQ. .NEQ. .BGT. .BLT. .BGE. .BLE.).

        Examples:
            >>> engine = AutoScriptEngine
            >>> user = {
            ...     "username": "test",
            ...     "enabled": True,
            ...     "reserve_info": {"date": "2026-05-07"}
            ... }
            >>> engine.execute(
            ...     'IF(CURRENT_TIME .BGT. TIME(19:00))\\n'
            ...     '    RESERVE_DATE .ADD. 1\\n'
            ...     'END IF',
            ...     user
            ... )
    """
    COMPARE_OPS = { # compare operators
        ".EQ." : lambda a, b: a == b,
        ".NEQ.": lambda a, b: a != b,
        ".BGT.": lambda a, b: a > b,
        ".BLT.": lambda a, b: a < b,
        ".BGE.": lambda a, b: a >= b,
        ".BLE.": lambda a, b: a <= b,
    }
    VARIABLE_META = { # variable metadata
        "预约开始时间": ("RESERVE_BEGIN_TIME", "Time"),
        "预约结束时间": ("RESERVE_END_TIME", "Time"),
        "预约日期": ("RESERVE_DATE", "Date"),
        "用户名":   ("USERNAME", "String"),
        "用户启用": ("USER_ENABLE", "Boolean"),
        "当前时间": ("CURRENT_TIME", "Time"),
        "当前日期": ("CURRENT_DATE", "Date"),
    }
    _FIELD_TYPE_MAP = {meta[0]: meta[1] for meta in VARIABLE_META.values()}

    @staticmethod
    def execute(
        script_text: str,
        user_data: dict
    ):
        """
            Execute an AutoScript against the given user data.

            The script is parsed line-by-line. All modifications are
            applied directly to ``user_data`` in-place.

            Args:
                script_text (str): Raw AutoScript source code.
                user_data (dict): User data dictionary to read from and
                    write to. Must conform to the standard user profile
                    structure (username, enabled, reserve_info, etc.).

            Raises:
                ValueError: On any syntax or type error encountered
                    during parsing or execution.
        """

        if not script_text or not script_text.strip():
            return
        lines = [l.strip() for l in script_text.split("\n") if l.strip()]
        if not lines:
            return
        if_stack = []

        for line in lines:
            upper_line = line.upper().strip()
            if upper_line.startswith("IF("):
                cond_end = _findConditionEnd(upper_line)
                if cond_end < 0:
                    raise ValueError("AutoScript 语法错误: IF 缺少右括号")
                condition_str = line[3:cond_end].strip()
                matched = AutoScriptEngine._evaluateCondition(
                    condition_str, user_data
                )
                if_stack.append([matched, matched])
            elif upper_line.startswith("ELSE IF("):
                if not if_stack:
                    raise ValueError("AutoScript 语法错误: ELSE IF 前缺少 IF")
                cond_end = _findConditionEnd(upper_line)
                if cond_end < 0:
                    raise ValueError("AutoScript 语法错误: ELSE IF 缺少右括号")
                condition_str = line[8:cond_end].strip()
                _, has_matched = if_stack[-1]
                if not has_matched:
                    matched = AutoScriptEngine._evaluateCondition(
                        condition_str, user_data
                    )
                    if_stack[-1] = [matched, matched]
                else:
                    if_stack[-1][0] = False
            elif upper_line == "ELSE":
                if not if_stack:
                    raise ValueError("AutoScript 语法错误: ELSE 前缺少 IF")
                _, has_matched = if_stack[-1]
                if not has_matched:
                    if_stack[-1] = [True, True]
                else:
                    if_stack[-1][0] = False
            elif upper_line in ("ENDIF", "END IF"):
                if not if_stack:
                    raise ValueError("AutoScript 语法错误: ENDIF/END IF 前缺少 IF")
                if_stack.pop()
            elif upper_line.startswith("SET "):
                should_execute = (
                    all(ctx[0] for ctx in if_stack) if if_stack else True
                )
                if should_execute:
                    AutoScriptEngine._executeSet(line, user_data)
            elif upper_line == "PASS":
                continue
            else:
                should_execute = (
                    all(ctx[0] for ctx in if_stack) if if_stack else True
                )
                if should_execute:
                    AutoScriptEngine._executeOperation(line, user_data)
        if if_stack:
            raise ValueError("AutoScript 语法错误: IF 与 ENDIF/END IF 不匹配")

    @staticmethod
    def _resolveField(
        field_name: str,
        user_data: dict
    ):

        upper_name = field_name.upper().strip()
        if upper_name == "CURRENT_DATE":
            return datetime.now().strftime("%Y-%m-%d")
        elif upper_name == "CURRENT_TIME":
            return datetime.now().strftime("%H:%M")
        elif upper_name == "USERNAME":
            return user_data.get("username", "")
        elif upper_name == "USER_ENABLE":
            return user_data.get("enabled", False)
        elif upper_name == "RESERVE_DATE":
            return user_data.get("reserve_info", {}).get("date", "")
        elif upper_name == "RESERVE_BEGIN_TIME":
            return (
                user_data
                .get("reserve_info", {})
                .get("begin_time", {})
                .get("time", "")
            )
        elif upper_name == "RESERVE_END_TIME":
            return (
                user_data
                .get("reserve_info", {})
                .get("end_time", {})
                .get("time", "")
            )
        return ""

    @staticmethod
    def _resolveValue(
        value_str: str,
        user_data: dict
    ):

        s = value_str.strip()
        time_match = re.match(r"^TIME\((\d{1,2}):(\d{2})\)$", s, re.IGNORECASE)
        if time_match:
            h, m = time_match.group(1), time_match.group(2)
            return f"{int(h):02d}:{int(m):02d}"
        date_match = re.match(r"^DATE\((\d{4})-(\d{2})-(\d{2})\)$", s, re.IGNORECASE)
        if date_match:
            y, mo, d = date_match.group(1), date_match.group(2), date_match.group(3)
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        if s.upper() == ".TRUE.":
            return True
        if s.upper() == ".FALSE.":
            return False
        if s.startswith("'") and s.endswith("'"):
            inner = s[1:-1].replace("''", "'")
            return inner
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        relDate = re.match(r"^CURRENT_DATE\s*\+\s*(\d+)$", s, re.IGNORECASE)
        if relDate:
            days = int(relDate.group(1))
            return (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        relTime = re.match(r"^CURRENT_TIME\s*\+\s*(\d+)$", s, re.IGNORECASE)
        if relTime:
            hours = int(relTime.group(1))
            return (datetime.now() + timedelta(hours=hours)).strftime("%H:%M")
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        resolved = AutoScriptEngine._resolveField(s, user_data)
        return resolved

    @staticmethod
    def _setField(
        field_name: str,
        value: str,
        user_data: dict
    ):
        upper_name = field_name.upper().strip()
        if upper_name == "RESERVE_DATE":
            user_data.setdefault("reserve_info", {})["date"] = value
        elif upper_name == "RESERVE_BEGIN_TIME":
            ri = user_data.setdefault("reserve_info", {})
            ri.setdefault("begin_time", {})["time"] = value
        elif upper_name == "RESERVE_END_TIME":
            ri = user_data.setdefault("reserve_info", {})
            ri.setdefault("end_time", {})["time"] = value
        elif upper_name == "USERNAME":
            user_data["username"] = value
        elif upper_name == "USER_ENABLE":
            if isinstance(value, bool):
                user_data["enabled"] = value
            else:
                user_data["enabled"] = (str(value).upper() == "TRUE")

    @staticmethod
    def _evaluateCondition(
        condition_str: str,
        user_data: dict
    ) -> bool:

        for op, cmp_func in AutoScriptEngine.COMPARE_OPS.items():
            if op not in condition_str.upper():
                continue
            idx = condition_str.upper().find(op)
            parts = [condition_str[:idx], condition_str[idx + len(op):]]
            if len(parts) != 2:
                continue
            field_name = parts[0].strip()
            value_str = parts[1].strip()
            left_val = AutoScriptEngine._resolveField(field_name, user_data)
            right_val = AutoScriptEngine._resolveValue(value_str, user_data)
            try:
                return cmp_func(left_val, right_val)
            except TypeError:
                raise ValueError(
                    f"AutoScript 语法错误: 无法比较 "
                    f"'{field_name}' ({type(left_val).__name__}) "
                    f"与 '{value_str}' ({type(right_val).__name__})"
                )
        return False

    @staticmethod
    def _executeSet(
        line: str,
        user_data: dict
    ):
        rest = line[3:].strip()
        eq_idx = rest.find("=")
        if eq_idx < 0:
            return
        field_name = rest[:eq_idx].strip()
        value_str = rest[eq_idx + 1:].strip()
        if not field_name:
            return
        resolved = AutoScriptEngine._resolveValue(value_str, user_data)
        AutoScriptEngine._setField(field_name, resolved, user_data)

    @staticmethod
    def _executeOperation(
        line: str,
        user_data: dict
    ):

        parts = line.split()
        if len(parts) < 3:
            return
        field_name = parts[0].upper().strip()
        op = parts[1].upper().strip()
        raw_value = parts[2].strip()
        field_type = AutoScriptEngine._FIELD_TYPE_MAP.get(field_name)
        if not field_type:
            raise ValueError(
                f"AutoScript 语法错误: 未知字段 '{field_name}'"
            )
        try:
            num_value = float(raw_value) if "." in raw_value else int(raw_value)
        except (ValueError, TypeError):
            raise ValueError(
                f"AutoScript 语法错误: 无效操作数 '{raw_value}'"
            )
        if field_type == "Date":
            date_str = AutoScriptEngine._resolveField(field_name, user_data)
            if not date_str:
                return
            try:
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            except (ValueError, TypeError):
                return
            if op == ".ADD.":
                date_obj += timedelta(days=num_value)
            elif op == ".SUB.":
                date_obj -= timedelta(days=num_value)
            else:
                raise ValueError(
                    f"AutoScript 语法错误: Date 类型不支持操作 '{op}'"
                )
            AutoScriptEngine._setField(
                field_name, date_obj.strftime("%Y-%m-%d"), user_data
            )
        elif field_type == "Time":
            time_str = AutoScriptEngine._resolveField(field_name, user_data)
            if not time_str:
                return
            try:
                time_obj = datetime.strptime(time_str, "%H:%M")
            except (ValueError, TypeError):
                return
            if op == ".ADD.":
                time_obj += timedelta(hours=num_value)
            elif op == ".SUB.":
                time_obj -= timedelta(hours=num_value)
            else:
                raise ValueError(
                    f"AutoScript 语法错误: Time 类型不支持操作 '{op}'"
                )
            AutoScriptEngine._setField(
                field_name, time_obj.strftime("%H:%M"), user_data
            )
        elif field_type in ("String", "Boolean"):
            raise ValueError(
                f"AutoScript 语法错误: '{field_type}' 类型字段不支持操作运算"
            )
        else:
            raise ValueError(
                f"AutoScript 语法错误: 未知字段类型 '{field_type}'"
            )


def _findConditionEnd(
    upper_line: str
) -> int:
    """
        Find the index of the closing parenthesis that matches the
        opening parenthesis in a condition expression, handling nested
        parentheses and optional ``THEN`` keyword.

        Args:
            upper_line (str): The uppercased line text containing the
                condition, e.g. ``"IF(A .BGT. B) THEN"``.

        Returns:
            int: Index of the matching ``)``, or ``-1`` if no match
            is found.
    """

    line = upper_line.rstrip()
    if line.endswith(" THEN"):
        line = line[:-5].rstrip()
    paren_depth = 0
    start_found = False
    for i, ch in enumerate(line):
        if ch == "(":
            paren_depth += 1
            start_found = True
        elif ch == ")":
            paren_depth -= 1
            if start_found and paren_depth == 0:
                return i
    return -1
