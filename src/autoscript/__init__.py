"""
    AutoScript module for the AutoLibrary project.
    A lightweight scripting DSL for preprocessing user reservation data.
"""
from autoscript.ASTokenizer import (
    ASTokenizer,
    Stmt,
    ElifNode,
    Script,
    IfNode,
    SetNode,
    OpNode,
)
from autoscript.ASEngine import (
    execute,
    addTargetVar,
)
from autoscript.ASObject import _META_VARS as META_VARS
from autoscript.ASObserver import ParsingObserver

__all__ = [
    "execute",
    "addTargetVar",
    "registerDefaultTargetVars",
    "buildMockTargetData",
    "META_VARS",
    "ALL_VARIABLES",
    "ASTokenizer",
    "Stmt",
    "Script",
    "IfNode",
    "SetNode",
    "OpNode",
    "ElifNode",
    "ParsingObserver",
]

# All variables available to scripts (display_name -> (name, type)).
# This mirrors the old AutoScriptEngine.VARIABLE_META for backward
# compatibility in the UI orchestration dialog.
ALL_VARIABLES: dict = {
    "用户名": ("USERNAME", "String"),
    "用户启用": ("USER_ENABLE", "Boolean"),
    "预约日期": ("RESERVE_DATE", "Date"),
    "预约开始时间": ("RESERVE_BEGIN_TIME", "Time"),
    "预约结束时间": ("RESERVE_END_TIME", "Time"),
    "当前时间": ("CURRENT_TIME", "Time"),
    "当前日期": ("CURRENT_DATE", "Date"),
}

# Key paths into target_data dict for each target variable.
# (name, type, key_path, display_name)
_TARGET_VAR_DEFS = [
    ("USERNAME",           "String",["username"],                           "用户名"),
    ("USER_ENABLE",        "Boolean",["enabled"],                           "用户启用"),
    ("RESERVE_DATE",       "Date",  ["reserve_info", "date"],               "预约日期"),
    ("RESERVE_BEGIN_TIME", "Time",  ["reserve_info", "begin_time", "time"], "预约开始时间"),
    ("RESERVE_END_TIME",   "Time",  ["reserve_info", "end_time",   "time"], "预约结束时间"),
]
_MOCK_TYPE_VALUES = {
    "String": "__mock__",
    "Boolean": True,
    "Date": "2099-01-01",
    "Time": "00:00",
    "Int": 0,
    "Float": 0.0,
}


def buildMockTargetData(
) -> dict:
    """
        Build a target_data dict filled with type-appropriate mock values
        for all registered target variables.
    """
    data = {}
    for _, var_type, key_path, _ in _TARGET_VAR_DEFS:
        d = data
        for key in key_path[:-1]:
            d = d.setdefault(key, {})
        d[key_path[-1]] = _MOCK_TYPE_VALUES.get(var_type, "")
    return data


def registerDefaultTargetVars(
) -> None:
    """
        Register all built-in target variables with the engine.
        This must be called before any script execution.
        Calling multiple times is idempotent (re-registers same keys).
    """
    for name, var_type, key_path, display_name in _TARGET_VAR_DEFS:
        addTargetVar(name, var_type, key_path, display_name)
