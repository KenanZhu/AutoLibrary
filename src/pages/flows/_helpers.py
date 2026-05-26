# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from datetime import datetime


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


def findBestTimeOption(
    time_options: list,
    target_time: int,
    max_time_diff: int,
    prefer_earlier: bool,
    is_reserve: bool = True,
) -> tuple:
    """
        Find the best time option from available WebElement options.

        Returns:
            (bestElement, bestText, actual_diff, freeTimesList)
            or (None, None, None, freeTimesList) if no suitable option.
    """

    free_times = []
    best_time_diff = max_time_diff
    best_actual_diff = None
    best_time_opt = None

    for time_opt in time_options:
        if is_reserve:
            time_attr = time_opt.get_attribute("time")
            if time_attr == "now":
                now = datetime.now()
                time_val = now.hour * 60 + now.minute
            elif time_attr and time_attr.isdigit():
                time_val = int(time_attr)
            else:
                continue
        else:
            time_attr = time_opt.get_attribute("id")
            if not (time_attr and time_attr.isdigit()):
                continue
            time_val = int(time_attr)
        free_times.append(
            time_opt.text.strip()
            if not is_reserve
            else minsToTimeStr(time_val)
        )
        actual_diff = time_val - target_time
        abs_diff = abs(actual_diff)
        if abs_diff < best_time_diff or (
            abs_diff == best_time_diff
            and (
                (prefer_earlier and actual_diff <= 0)
                or (not prefer_earlier and actual_diff >= 0)
            )
        ):
            best_time_diff = abs_diff
            best_actual_diff = actual_diff
            best_time_opt = time_opt
    if best_time_opt is not None:
        return (best_time_opt, best_time_opt.text.strip(), best_actual_diff, free_times)
    return (None, None, None, free_times)
