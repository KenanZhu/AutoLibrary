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

from autoscript._helpers import (
    _TYPE_DEFAULT_VAR,
    _assignPath,
    _checkDateFormat,
    _checkTimeFormat,
    _checkType,
    _cleanLuaError,
    _navigatePath,
)

try:
    from lupa.lua55 import LuaError as _LuaError, LuaSyntaxError as _LuaSyntaxError
except ImportError:
    try:
        from lupa.lua54 import LuaError as _LuaError, LuaSyntaxError as _LuaSyntaxError
    except ImportError:
        _LuaError = Exception
        _LuaSyntaxError = Exception


__all__ = ["ASEngine"]


class ASEngine:

    @staticmethod
    def getCurrentDate(
    ) -> str:

        return date.today().isoformat()

    @staticmethod
    def getCurrentTime(
    ) -> str:

        return datetime.now().strftime("%H:%M")

    @staticmethod
    def _sandbox(
        lua,
    ) -> None:

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

    @staticmethod
    def _registerHelpers(
        lua,
    ) -> None:

        lua.execute("""
            function date(y, m, d)
                return os.time({year = y, month = m, day = d})
            end

            function time(h, m)
                return h * 60 + m
            end

            function datenow()
                local now = os.date("*t")
                return os.time({year = now.year, month = now.month, day = now.day})
            end

            function timenow()
                local now = os.date("*t")
                return now.hour * 60 + now.min
            end

            function dateadd(date_val, n)
                return date_val + n * 86400
            end

            function timeadd(time_val, n)
                return (time_val + n * 60) % 1440
            end

            function strtodate(iso_str)
                local y, m, d = iso_str:match("(%d+)-(%d+)-(%d+)")
                return os.time({year = y, month = m, day = d})
            end

            function strtotime(hm_str)
                local h, m = hm_str:match("(%d+):(%d+)")
                return h * 60 + m
            end

            function datetostr(ts)
                return os.date("%Y-%m-%d", ts)
            end

            function timetostr(m)
                return string.format("%02d:%02d", math.floor(m / 60), m % 60)
            end
        """)

    def __init__(
        self,
        targetVars: list[tuple] = None,
    ):

        self._targetVars: dict[str, dict] = {}
        self._lua = None

        if targetVars:
            for item in targetVars:
                name, varType, keyPath = item[0], item[1], item[2]
                self.addTargetVar(name, varType, keyPath)

    def _getLua(
        self,
    ):

        if self._lua is None:
            self._lua = _LuaRuntime(unpack_returned_tuples=True)
            self._sandbox(self._lua)
            self._registerHelpers(self._lua)
        return self._lua

    def _push(
        self,
        targetData: dict,
    ) -> None:

        lua = self._getLua()
        g = lua.globals()
        strToDate = g["strtodate"]
        strToTime = g["strtotime"]

        for varName, info in self._targetVars.items():
            keyPath = info["keyPath"]
            vt = info["type"]
            raw = _navigatePath(targetData, keyPath)
            if vt == "Date":
                if not isinstance(raw, str) or not raw.strip():
                    raise ValueError(
                        f"Date 类型变量 '{varName}' 对应的数据为空或不是字符串类型，"
                        f"请检查路径 {keyPath} 的值是否为合法的日期字符串 (YYYY-MM-DD)"
                    )
                raw = raw.strip()
                _checkDateFormat(raw, varName)
                g[varName] = strToDate(raw)
            elif vt == "Time":
                if not isinstance(raw, str) or not raw.strip():
                    raise ValueError(
                        f"Time 类型变量 '{varName}' 对应的数据为空或不是字符串类型，"
                        f"请检查路径 {keyPath} 的值是否为合法的时间字符串 (HH:MM)"
                    )
                raw = raw.strip()
                _checkTimeFormat(raw, varName)
                g[varName] = strToTime(raw)
            else:
                if raw is None:
                    raw = _TYPE_DEFAULT_VAR.get(vt, False)
                g[varName] = raw

    def _pull(
        self,
        targetData: dict,
    ) -> None:

        lua = self._getLua()
        g = lua.globals()
        dateToStr = g["datetostr"]
        timeToStr = g["timetostr"]

        for varName, info in self._targetVars.items():
            try:
                luaVal = g[varName]
            except KeyError:
                continue
            vt = info["type"]
            if vt == "Date":
                luaVal = dateToStr(luaVal)
            elif vt == "Time":
                luaVal = timeToStr(luaVal)
            elif vt == "Float" and isinstance(luaVal, int) and not isinstance(luaVal, bool):
                luaVal = float(luaVal)
            _checkType(varName, vt, luaVal)
            _assignPath(targetData, info["keyPath"], luaVal)

    def addTargetVar(
        self,
        name: str,
        varType: str,
        keyPath: list,
    ) -> None:

        upperName = name.upper().strip()
        self._targetVars[upperName] = {
            "type": varType,
            "keyPath": keyPath,
        }

    def execute(
        self,
        scriptText: str,
        targetData: dict,
    ) -> None:

        if not scriptText or not scriptText.strip():
            return
        try:
            self._push(targetData)
            self._getLua().execute(scriptText)
            self._pull(targetData)
        except _LuaSyntaxError as e:
            raise ValueError(
                f"AutoScript 语法错误: {_cleanLuaError(str(e))}"
            )
        except _LuaError as e:
            raise ValueError(
                f"AutoScript 运行时错误: {_cleanLuaError(str(e))}"
            )
        except ValueError as e:
            raise ValueError(f"AutoScript 数据错误: {e}")
        except Exception as e:
            raise ValueError(f"AutoScript 未知错误: {e}")

    def reset(
        self,
    ) -> None:

        self._targetVars = {}
        self._lua = None
