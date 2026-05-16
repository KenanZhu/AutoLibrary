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
    date,
    time
)


__all__ = [
    "ASObject",
    "_META_VARS",
    "_inferType"
]


# Default values for each supported type when no value is present
_TYPE_DEFAULTS = {
    "Int": 0,
    "Float": 0.0,
    "Boolean": False,
    "Date": None,
    "Time": None,
    "String": ""
}


class ASObject:
    """
        Represents a variable object used throughout the AutoScript engine.

        An ASObject can be a meta variable (read-only, e.g. CURRENT_DATE),
        a target variable (bound to a config data dict via key_path),
        or a script variable (free-form, stored internally).

        Args:
            name (str): The canonical name of the variable (case-insensitive).
            var_type (str): One of "Int", "Float", "Boolean", "Date", "Time", "String".
            read_only (bool): Whether the variable is read-only (default: False).
            is_config (bool): Whether the variable maps to a target_data path (default: False).
            key_path (list): The nested key path into target_data, e.g. ["reserve_info", "date"].
            default_value: The fallback value when no target_data value is found.
            display_name (str): An alias for use in script conditions and assignments.

        Example:
            >>> obj = ASObject("MY_DATE", "Date", is_config=True,
            ...                key_path=["reserve_info", "date"],
            ...                display_name="预约日期")
            >>> obj.getValue({"reserve_info": {"date": "2026-05-01"}})
            datetime.date(2026, 5, 1)
    """

    _TEMP_COUNTER = 0

    def __init__(
        self,
        name: str,
        var_type: str, *,
        read_only: bool = False,
        is_config: bool = False,
        key_path: list = None,
        default_value=None,
        display_name: str = None
    ):

        self.name = name
        self.var_type = var_type
        self.read_only = read_only
        self.is_config = is_config
        self.key_path = key_path or []
        self._value = default_value
        self.display_name = display_name

    @classmethod
    def _makeTemp(
        cls,
        value,
        inferred_type: str
    ):
        """
            Create a temporary unnamed ASObject from a literal value.

            Temporary objects are used for inline script literals (e.g. 42,
            'hello', DATE(2026-01-01)) so they can participate in typed
            operations alongside registered variables.

            Args:
                value: The resolved Python value.
                inferred_type (str): The AutoScript type name.

            Returns:
                ASObject: A temporary, non-config, read-write ASObject.
        """

        cls._TEMP_COUNTER += 1
        return cls(
            f"__TMP_{cls._TEMP_COUNTER}",
            inferred_type,
            read_only=False,
            is_config=False,
            default_value=value
        )


    def _typeEmpty(
        self
    ):
        """
            Return the type-appropriate empty / default value.
        """

        return _TYPE_DEFAULTS.get(self.var_type, "")


    def getValue(
        self,
        target_data: dict = None
    ):
        """
            Retrieve the current value of this variable.

            For read-only variables (CURRENT_DATE, CURRENT_TIME), returns the
            live datetime. For config variables, traverses the key_path into
            target_data and parses Date/Time strings. Otherwise returns the
            internal _value.

            Args:
                target_data (dict): The application data dict (required for config vars).

            Returns:
                The resolved value, or a type-appropriate default if missing.
        """

        if self.read_only:
            if self.name == "CURRENT_DATE":
                return datetime.now().date()
            if self.name == "CURRENT_TIME":
                return datetime.now().time()
            return self._value
        if self.is_config and target_data is not None and self.key_path:
            d = target_data
            for key in self.key_path[:-1]:
                d = d.get(key, {})
                if not isinstance(d, dict):
                    return self._typeEmpty()
            raw = d.get(self.key_path[-1])
            if raw is None:
                return self._typeEmpty()
            if self.var_type == "Date" and isinstance(raw, str):
                try:
                    return datetime.strptime(raw, "%Y-%m-%d").date()
                except ValueError:
                    return self._typeEmpty()
            if self.var_type == "Time" and isinstance(raw, str):
                try:
                    return datetime.strptime(raw, "%H:%M").time()
                except ValueError:
                    return self._typeEmpty()
            return raw
        return self._value


    def setValue(
        self,
        value,
        target_data: dict = None
    ):
        """
            Assign a new value to this variable, with type coercion.

            Performs coercion for Boolean (string -> bool), Int, and Float types.
            For config variables, dates/times are converted back to strings before
            writing into target_data.

            Args:
                value: The value to assign.
                target_data (dict): The application data dict (required for config vars).

            Raises:
                ValueError: If the variable is read-only or value cannot be coerced.
        """

        if self.read_only:
            raise ValueError(f"不能修改只读变量 '{self.name}'")
        if self.var_type == "Boolean" and not isinstance(value, bool):
            value = (str(value).upper() == "TRUE")
        if self.var_type == "Int" and not isinstance(value, int):
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise ValueError(f"无法将值 '{value}' 转换为 Int 类型")
        if self.var_type == "Float" and not isinstance(value, float):
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise ValueError(f"无法将值 '{value}' 转换为 Float 类型")
        if self.is_config:
            if self.var_type == "Date" and isinstance(value, date):
                value = value.strftime("%Y-%m-%d")
            if self.var_type == "Time" and isinstance(value, time):
                value = value.strftime("%H:%M")
        if self.is_config and target_data is not None and self.key_path:
            d = target_data
            for key in self.key_path[:-1]:
                d = d.setdefault(key, {})
            d[self.key_path[-1]] = value
        else:
            self._value = value


# Built-in read-only meta variables available to all scripts
_META_VARS = {
    "CURRENT_DATE": ASObject("CURRENT_DATE", "Date", read_only=True, display_name="当前日期"),
    "CURRENT_TIME": ASObject("CURRENT_TIME", "Time", read_only=True, display_name="当前时间"),
}


def _inferType(
    value,
    raw_expr: str = None
) -> str:
    """
        Infer the ASObject type string from a Python value or raw expression.

        When the Python type is ambiguous (e.g. int can be Int or a component
        of Date), the raw_expr is used as a hint.

        Args:
            value: The resolved Python value.
            raw_expr (str): The original expression string from the script (optional).

        Returns:
            str: One of "Boolean", "Int", "Float", "Date", "Time", "String".
    """

    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int):
        return "Int"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, date):
        return "Date"
    if isinstance(value, time):
        return "Time"
    if raw_expr:
        if re.match(r"^DATE\(\d{4}-\d{2}-\d{2}\)$", raw_expr, re.IGNORECASE):
            return "Date"
        if re.match(r"^TIME\(\d{1,2}:\d{2}\)$", raw_expr, re.IGNORECASE):
            return "Time"
    return "String"
