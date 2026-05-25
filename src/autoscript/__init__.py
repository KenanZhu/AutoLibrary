# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from autoscript.ASEngine import ASEngine


__all__ = [
    "ASEngine",
    "createEngine",
    "createMockTargetData",
    "createAllVariablesTable",
    "createTargetVarDefs",
]


_TARGET_VAR_DEFS = [
    ("USERNAME",           "String",  ["username"],                           "用户名"),
    ("USER_ENABLE",        "Boolean", ["enabled"],                            "用户启用"),
    ("RESERVE_DATE",       "Date",    ["reserve_info", "date"],               "预约日期"),
    ("RESERVE_BEGIN_TIME", "Time",    ["reserve_info", "begin_time", "time"], "预约开始时间"),
    ("RESERVE_END_TIME",   "Time",    ["reserve_info", "end_time",   "time"], "预约结束时间"),
]
_MOCK_TYPE_VALUES = {
    "String": "__mock__",
    "Boolean": True,
    "Date": "2099-01-01",
    "Time": "00:00",
    "Int": 0,
    "Float": 0.0,
}


def createAllVariablesTable(
) -> dict:

    return {
        displayName: (name, varType)
        for name, varType, _, displayName in _TARGET_VAR_DEFS
    }

def createTargetVarDefs(
) -> list:

    return list(_TARGET_VAR_DEFS)

def createMockTargetData(
) -> dict:

    data = {}
    for _, varType, keyPath, _ in _TARGET_VAR_DEFS:
        d = data
        for key in keyPath[:-1]:
            d = d.setdefault(key, {})
        d[keyPath[-1]] = _MOCK_TYPE_VALUES.get(varType, "")
    return data

def createEngine(
) -> ASEngine:

    return ASEngine(_TARGET_VAR_DEFS)
