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

from lupa import LuaRuntime as _LuaRuntime


__all__ = ["execute", "addTargetVar", "resetEngine"]


# Engine state
_TARGET_VARS: dict[str, dict] = {}
_lua = None

# Built-in meta variable definitions (name / type / display-name)
META_VARS = {
    "CURRENT_DATE": {"name": "CURRENT_DATE", "type": "Date", "display": "当前日期"},
    "CURRENT_TIME": {"name": "CURRENT_TIME", "type": "Time", "display": "当前时间"},
}


def _getLua(
):
    """
        Return the sandboxed Lua runtime singleton.
    """

    global _lua
    if _lua is None:
        _lua = _LuaRuntime(unpack_returned_tuples = True)
        _sandbox(_lua)
        _registerHelpers(_lua)
    return _lua


def _sandbox(
    lua,
) -> None:
    """
        Remove dangerous Lua globals while keeping os.date / os.time for date-time helpers.
    """

    lua.execute("""
        io = nil
        require = nil
        dofile = nil
        loadfile = nil
        load = nil
        package = nil
        rawget = nil
        rawset = nil
        rawequal = nil
        getfenv = nil
        setfenv = nil
        debug = nil
        -- selectively disable dangerous os functions, keep date / time
        if os then
            os.execute = nil
            os.exit = nil
            os.getenv = nil
            os.remove = nil
            os.rename = nil
            os.tmpname = nil
            os.setlocale = nil
        end
    """)


def _registerHelpers(
    lua,
) -> None:
    """
        Inject Date / Time helpers as pure Lua functions.

        Date values are os.time timestamps (seconds since epoch).
        Time values are minutes since midnight (0-1439).

        This keeps Date / Time as native Lua numbers during script execution,
        enabling type-safe arithmetic (+, -) and comparisons (<, <=, ==, ~=).
    """

    lua.execute("""
        function date(y, m, d)
            return os.time({year = y, month = m, day = d})
        end

        function time(h, m)
            return h * 60 + m
        end

        function CURRENT_DATE()
            local now = os.date("*t")
            return os.time({year = now.year, month = now.month, day = now.day})
        end

        function CURRENT_TIME()
            local now = os.date("*t")
            return now.hour * 60 + now.min
        end

        function date_add(date_val, n)
            return date_val + n * 86400
        end

        function time_add(time_val, n)
            return (time_val + n * 60) % 1440
        end

        -- push helpers: string -> native type
        function _to_date(iso_str)
            local y, m, d = iso_str:match("(%d+)-(%d+)-(%d+)")
            return os.time({year = y, month = m, day = d})
        end

        function _to_time(hm_str)
            local h, m = hm_str:match("(%d+):(%d+)")
            return h * 60 + m
        end

        -- pull helpers: native type -> string
        function _from_date(ts)
            return os.date("%Y-%m-%d", ts)
        end

        function _from_time(m)
            return string.format("%02d:%02d", math.floor(m / 60), m % 60)
        end
    """)


def _navigatePath(
    data: dict,
    key_path: list,
    default = None,
):
    """
        Walk *key_path* into *data* and return the value at the leaf.
    """

    d = data
    for key in key_path[:-1]:
        d = d.get(key, {})
        if not isinstance(d, dict):
            return default
    return d.get(key_path[-1], default)


def _assignPath(
    data: dict,
    key_path: list,
    value,
) -> None:
    """
        Walk *key_path* into *data* and set *value* at the leaf.
    """

    d = data
    for key in key_path[:-1]:
        d = d.setdefault(key, {})
    d[key_path[-1]] = value


def _checkType(
    var_name: str,
    var_type: str,
    value,
) -> None:
    """
        Validate that *value* matches the declared variable type.

        Date / Time values arrive as ISO / HH:MM strings (already converted
        from Lua native types during the pull phase).
        Int / Float / Boolean / String check Python type identity.
        Int -> Float widening is allowed.
    """

    if var_type == "Date":
        if not isinstance(value, str):
            raise ValueError(
                f"Date 类型变量 '{var_name}' 只能接受日期字符串，"
                f"不能接受 {type(value).__name__} 类型"
            )
        date.fromisoformat(value)
        return
    if var_type == "Time":
        if not isinstance(value, str):
            raise ValueError(
                f"Time 类型变量 '{var_name}' 只能接受时间字符串，"
                f"不能接受 {type(value).__name__} 类型"
            )
        datetime.strptime(value, "%H:%M")
        return
    if var_type == "Int":
        if isinstance(value, bool):
            raise ValueError(
                f"Int 类型变量 '{var_name}' 不能接受 Boolean 类型的值"
            )
        if not isinstance(value, int) and not (isinstance(value, float) and value == int(value)):
            raise ValueError(
                f"Int 类型变量 '{var_name}' 不能接受 {type(value).__name__} 类型的值"
            )
        return
    if var_type == "Float":
        if isinstance(value, bool):
            raise ValueError(
                f"Float 类型变量 '{var_name}' 不能接受 Boolean 类型的值"
            )
        if not isinstance(value, (int, float)):
            raise ValueError(
                f"Float 类型变量 '{var_name}' 不能接受 {type(value).__name__} 类型的值"
            )
        return
    if var_type == "Boolean":
        if not isinstance(value, bool):
            raise ValueError(
                f"Boolean 类型变量 '{var_name}' 不能接受 {type(value).__name__} 类型的值"
            )
        return
    if var_type == "String":
        if not isinstance(value, str):
            raise ValueError(
                f"String 类型变量 '{var_name}' 不能接受 {type(value).__name__} 类型的值"
            )
        return


def addTargetVar(
    name: str,
    var_type: str,
    key_path: list,
    display_name: str = None,
) -> None:
    """
        Register a new target variable bound to a path in the application data dict.

        Args:
            name (str): The canonical variable name (e.g. "RESERVE_DATE").
            var_type (str): "Int" | "Float" | "Boolean" | "Date" | "Time" | "String".
            key_path (list): Nested path into target_data, e.g. ["reserve_info", "date"].
            display_name (str): Optional Chinese alias (unused by the engine).
    """

    upper_name = name.upper().strip()
    _TARGET_VARS[upper_name] = {
        "type": var_type,
        "key_path": key_path,
    }


def resetEngine(
) -> None:
    """
        Reset the engine to its initial state: clear all target variables
        and release the Lua runtime.
    """
    global _TARGET_VARS, _lua
    _TARGET_VARS = {}
    _lua = None


def _push(
    target_data: dict,
) -> None:
    """
        Push target_data values into Lua globals.
        Date / Time strings are converted to native Lua types (timestamp / minutes).
    """

    lua = _getLua()
    g = lua.globals()
    _toDate = g["_to_date"]
    _toTime = g["_to_time"]

    for var_name, info in _TARGET_VARS.items():
        key_path = info["key_path"]
        vt = info["type"]
        raw = _navigatePath(target_data, key_path)

        if vt == "Date":
            if raw and isinstance(raw, str):
                try:
                    date.fromisoformat(raw.strip())
                except (ValueError, AttributeError):
                    raw = "2099-01-01"
            else:
                raw = "2099-01-01"
            g[var_name] = _toDate(raw)
        elif vt == "Time":
            if raw and isinstance(raw, str):
                try:
                    datetime.strptime(raw.strip(), "%H:%M")
                except (ValueError, AttributeError):
                    raw = "00:00"
            else:
                raw = "00:00"
            g[var_name] = _toTime(raw)
        else:
            if raw is None:
                raw = "" if vt == "String" else 0 if vt == "Int" else 0.0 if vt == "Float" else False
            g[var_name] = raw


def _pull(
    target_data: dict,
) -> None:
    """
        Pull Lua global values back into target_data.
        Date / Time native types are converted back to ISO / HH:MM strings.
    """

    lua = _getLua()
    g = lua.globals()
    _fromDate = g["_from_date"]
    _fromTime = g["_from_time"]

    for var_name, info in _TARGET_VARS.items():
        try:
            lua_val = g[var_name]
        except (KeyError, AttributeError):
            continue
        vt = info["type"]
        if vt == "Date":
            lua_val = _fromDate(lua_val)
        elif vt == "Time":
            lua_val = _fromTime(lua_val)
        elif vt == "Float" and isinstance(lua_val, int) and not isinstance(lua_val, bool):
            lua_val = float(lua_val)
        _checkType(var_name, vt, lua_val)
        _assignPath(target_data, info["key_path"], lua_val)


def execute(
    script_text: str,
    target_data: dict,
) -> None:
    """
        Execute an AutoScript (Lua) on the given target data.

        The script runs in a sandboxed Lua environment with target variables
        exposed as globals.  The following helpers are available as Lua functions:

          date(y, m, d)         -> timestamp (os.time seconds)
          time(h, m)            -> minutes since midnight (0-1439)
          CURRENT_DATE()        -> today's timestamp
          CURRENT_TIME()        -> current minutes since midnight
          date_add(ts, n)       -> ts + n * 86400
          time_add(m, n)        -> (m + n * 60) % 1440

        Date and Time values are native Lua numbers during execution.
        Arithmetic (+, -) and comparisons (<, <=, ==, ~=, >, >=) work
        with strong type safety — no implicit string coercion.

        Raises:
            ValueError: On Lua compilation/runtime errors or type mismatches.
    """

    if not script_text or not script_text.strip():
        return
    _push(target_data)
    try:
        _getLua().execute(script_text)
        _pull(target_data)
    except Exception as e:
        raise ValueError(f"AutoScript 执行错误: {e}")
