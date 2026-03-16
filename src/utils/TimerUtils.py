# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from datetime import datetime, timedelta


def calculateNextRepeatTime(
    repeat_days: list,
    hour: int,
    minute: int,
    second: int
) -> datetime:
    """
        Calculate the next repeat time based on repeat days and target time.

        This function calculates the next execution time for a repeatable task.
        If the current day is in repeat_days and the target time has not passed,
        it returns today's target time. Otherwise, it finds the next matching day.

        Args:
            repeat_days (list): List of weekdays to repeat (0=Monday, 6=Sunday).
            hour (int): Target hour (0-23).
            minute (int): Target minute (0-59).
            second (int): Target second (0-59).

        Returns:
            datetime: The next repeat execution time.
    """

    current_time = datetime.now()
    current_weekday = current_time.weekday()
    target_time = current_time.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if current_weekday in repeat_days:
        if target_time > current_time:
            return target_time
    repeat_days_sorted = sorted(repeat_days)
    for day in repeat_days_sorted:
        if day > current_weekday:
            days_until = day - current_weekday
            next_time = target_time + timedelta(days=days_until)
            return next_time
    days_until = 7 - current_weekday + repeat_days_sorted[0]
    next_time = target_time + timedelta(days=days_until)
    return next_time
