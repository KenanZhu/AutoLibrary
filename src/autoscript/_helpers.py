# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from datetime import (
    date,
    datetime,
)


_TYPE_DEFAULT_VAR: dict[str, str | int | float | bool] = {
    "String": "",
    "Int": 0,
    "Float": 0.0,
    "Boolean": False,
}


def _navigatePath(
    data: dict,
    keyPath: list,
    default=None,
):

    d = data
    for key in keyPath[:-1]:
        d = d.get(key, {})
        if not isinstance(d, dict):
            return default
    return d.get(keyPath[-1], default)

def _assignPath(
    data: dict,
    keyPath: list,
    value,
) -> None:

    d = data
    for key in keyPath[:-1]:
        d = d.setdefault(key, {})
    d[keyPath[-1]] = value

def _checkDateFormat(
    dateStr: str,
    varName: str = "",
) -> None:

    prefix = f"Date 类型变量 '{varName}' 的" if varName else ""
    try:
        date.fromisoformat(dateStr)
    except ValueError:
        raise ValueError(
            f"{prefix}值 '{dateStr}' 不是合法的日期格式，"
            f"应为 YYYY-MM-DD"
        )

def _checkTimeFormat(
    timeStr: str,
    varName: str = "",
) -> None:

    prefix = f"Time 类型变量 '{varName}' 的" if varName else ""
    try:
        datetime.strptime(timeStr, "%H:%M")
    except ValueError:
        raise ValueError(
            f"{prefix}值 '{timeStr}' 不是合法的时间格式，"
            f"应为 HH:MM"
        )

def _checkType(
    varName: str,
    varType: str,
    value,
) -> None:

    if varType == "Date":
        if not isinstance(value, str):
            raise ValueError(
                f"Date 类型变量 '{varName}' 只能接受日期字符串，"
                f"不能接受 {_pyTypeToASType(value)} 类型"
            )
        _checkDateFormat(value, varName)
        return
    if varType == "Time":
        if not isinstance(value, str):
            raise ValueError(
                f"Time 类型变量 '{varName}' 只能接受时间字符串，"
                f"不能接受 {_pyTypeToASType(value)} 类型"
            )
        _checkTimeFormat(value, varName)
        return
    if varType == "Int":
        if isinstance(value, bool):
            raise ValueError(
                f"Int 类型变量 '{varName}' 不能接受 Boolean 类型的值"
            )
        if not isinstance(value, int) and not (isinstance(value, float) and value == int(value)):
            raise ValueError(
                f"Int 类型变量 '{varName}' 不能接受 {_pyTypeToASType(value)} 类型的值"
            )
        return
    if varType == "Float":
        if isinstance(value, bool):
            raise ValueError(
                f"Float 类型变量 '{varName}' 不能接受 Boolean 类型的值"
            )
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Float 类型变量 '{varName}' 不能接受 {_pyTypeToASType(value)} 类型的值"
            )
        return
    if varType == "Boolean":
        if not isinstance(value, bool):
            raise ValueError(
                f"Boolean 类型变量 '{varName}' 不能接受 {_pyTypeToASType(value)} 类型的值"
            )
        return
    if varType == "String":
        if not isinstance(value, str):
            raise ValueError(
                f"String 类型变量 '{varName}' 不能接受 {_pyTypeToASType(value)} 类型的值"
            )
        return

def _pyTypeToASType(
    value,
) -> str:

    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, int):
        return "Int"
    if isinstance(value, float):
        return "Float"
    if isinstance(value, str):
        return "String"
    return "Unknown"

def _cleanLuaError(
    rawMsg: str,
) -> str:

    msg = rawMsg.replace('[string "<python>"]:', "").strip()
    stackIdx = msg.find("stack traceback:")
    if stackIdx != -1:
        msg = msg[:stackIdx].strip()
    return msg
