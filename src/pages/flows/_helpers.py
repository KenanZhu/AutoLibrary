# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
def timeStrToMins(
    time_str: str,
) -> int:

    hour, minute = map(int, time_str.split(":"))
    return hour * 60 + minute

def minsToTimeStr(
    mins: int,
) -> str:

    hour, minute = divmod(int(mins), 60)
    return f"{hour:02d}:{minute:02d}"
