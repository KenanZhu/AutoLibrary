# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from datetime import (
    datetime,
    timedelta,
    date,
    time
)

from .ASObject import ASObject


__all__ = ["ASOperator"]


class ASOperator:
    """
        Centralised type-safe operations for AutoScript engine types.

        All arithmetic (ADD / SUB) and comparison operators are routed through
        this class, which dispatches to the correct Python-level logic based on
        the ASObject's var_type.  This keeps type-specific branching in one
        place instead of scattering it across the engine.

        Args:
            op (str): One of ".ADD.", ".SUB.", ".EQ.", ".NEQ.", ".BGT.",
                      ".BLT.", ".BGE.", ".BLE.".

        Example:
            >>> obj = ASObject("X", "Int", default_value=10)
            >>> ASOperator.apply(obj, ASObject._makeTemp(5, "Int"), ".ADD.", None)
            >>> obj.getValue()
            15
            >>> ASOperator.compare(
            ...     obj,
            ...     ASObject._makeTemp(15, "Int"),
            ...     ".EQ.", None
            ... )
            True
    """

    _COMPARE = {
        ".EQ." : lambda a, b: a == b,
        ".NEQ.": lambda a, b: a != b,
        ".BGT.": lambda a, b: a > b,
        ".BLT.": lambda a, b: a < b,
        ".BGE.": lambda a, b: a >= b,
        ".BLE.": lambda a, b: a <= b,
    }
    _ARITH_TYPES = {"Date", "Time", "Int", "Float"}
    # Comparison-compatible type groups
    _COMPATIBLE_GROUPS = [
        {"String"},
        {"Boolean"},
        {"Int", "Float"},
        {"Date"},
        {"Time"},
    ]

    @classmethod
    def apply(
        cls,
        target: ASObject,
        operand: ASObject,
        op: str,
        target_data: dict
    ):
        """
            Apply ADD or SUB to a target ASObject, modifying it in place.

            Args:
                target (ASObject): The variable to modify.
                operand (ASObject): The operand (numeric value for Date/Time/Int/Float).
                op (str): ".ADD." or ".SUB.".
                target_data (dict): Application data dict (passed through to getValue/setValue).

            Raises:
                ValueError: If the type does not support the operation or values are invalid.
        """

        tp = target.var_type
        op_tp = operand.var_type
        if tp not in cls._ARITH_TYPES:
            raise ValueError(f"'{tp}' 类型字段不支持操作运算")
        if op_tp not in ("Int", "Float"):
            raise ValueError(f"操作数类型 '{op_tp}' 不能用于运算，需要数值类型 (Int / Float)")
        if tp in ("Date", "Time") and op_tp != "Int":
            raise ValueError(f"'{tp}' 类型的加减法操作数必须为 Int 类型，不允许 Float")
        target_val = target.getValue(target_data)
        if target_val is None:
            raise ValueError(f"'{target.name}' 的值为空，无法进行运算")
        if op == ".ADD.":
            cls._arithAdd(target, target_val, operand, target_data)
        elif op == ".SUB.":
            cls._arithSub(target, target_val, operand, target_data)
        else:
            raise ValueError(f"不支持的操作 '{op}'")

    @classmethod
    def _arithBinary(
        cls,
        target: ASObject,
        target_val,
        operand: ASObject,
        target_data: dict,
        sign: int
    ):
        """Apply ADD (sign=1) or SUB (sign=-1) per type."""

        tp = target.var_type
        raw_op = operand._value
        op_name = "ADD" if sign == 1 else "SUB"

        if tp == "Date":
            if not isinstance(target_val, date):
                raise ValueError(f"'{target.name}' 的值 '{target_val}' 不是有效日期")
            new_val = target_val + timedelta(days=int(raw_op)) * sign
        elif tp == "Time":
            if not isinstance(target_val, time):
                raise ValueError(f"'{target.name}' 的值 '{target_val}' 不是有效时间")
            delta = timedelta(hours=int(raw_op)) * sign
            dt = datetime.combine(datetime.today(), target_val) + delta
            new_val = dt.time()
        elif tp == "Int":
            new_val = int(target_val) + int(raw_op) * sign
        elif tp == "Float":
            new_val = float(target_val) + float(raw_op) * sign
        else:
            raise ValueError(f"'{tp}' 类型不支持 {op_name} 操作")
        target.setValue(new_val, target_data)

    @classmethod
    def _arithAdd(
        cls,
        target: ASObject,
        target_val,
        operand: ASObject,
        target_data: dict
    ):
        """Dispatch ADD per type."""
        cls._arithBinary(target, target_val, operand, target_data, 1)

    @classmethod
    def _arithSub(
        cls,
        target: ASObject,
        target_val,
        operand: ASObject,
        target_data: dict
    ):
        """Dispatch SUB per type."""
        cls._arithBinary(target, target_val, operand, target_data, -1)

    @classmethod
    def compare(
        cls,
        left: ASObject,
        right: ASObject,
        op: str,
        target_data: dict
    ) -> bool:
        """
            Compare two ASObjects using the given comparison operator.

            Args:
                left (ASObject): Left-hand side.
                right (ASObject): Right-hand side.
                op (str): One of ".EQ.", ".NEQ.", ".BGT.", ".BLT.", ".BGE.", ".BLE.".
                target_data (dict): Application data dict.

            Returns:
                bool: The comparison result.

            Raises:
                ValueError: If the types are incompatible for comparison.
        """

        cmp_func = cls._COMPARE.get(op)
        if cmp_func is None:
            raise ValueError(f"未知的比较操作 '{op}'")
        left_tp = left.var_type
        right_tp = right.var_type
        if left_tp != right_tp:
            same_group = any(
                left_tp in g and right_tp in g
                for g in cls._COMPATIBLE_GROUPS
            )
            if not same_group:
                raise ValueError(
                    f"类型不兼容: 无法将 '{left.name}' ({left_tp}) "
                    f"与 '{right.name}' ({right_tp}) 进行比较"
                )
        left_val = left.getValue(target_data)
        right_val = right.getValue(target_data)
        try:
            return cmp_func(left_val, right_val)
        except TypeError:
            raise ValueError(
                f"无法比较 '{left.name}' ({left.var_type}) "
                f"与 '{right.name}' ({right.var_type})"
            )
