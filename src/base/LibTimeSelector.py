# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from base.LibOperator import LibOperator


class LibTimeSelector(LibOperator):
    """
        Base class for time selection operations.

        This class provides common time selection logic for reservation and renewal
        operations, including time conversion utilities and best time option finding.
    """

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue
    ):

        super().__init__(input_queue, output_queue)

    @staticmethod
    def _timeToMins(
        time_str: str
    ) -> int:

        """
            Convert time string "HH:MM" to minutes since midnight.
        """
        hour, minute = map(int, time_str.split(":"))
        return hour*60 + minute

    @staticmethod
    def _minsToTime(
        mins: int
    ) -> str:

        """
            Convert minutes since midnight to time string "HH:MM".
        """
        hour, minute = divmod(mins, 60)
        return f"{hour:02d}:{minute:02d}"


    def _formatTimeRelation(
        self,
        abs_diff: int,
        actual_diff: int,
        time_type: str
    ) -> str:

        """
            Format time difference relation string.
        """
        if actual_diff < 0:
            return f"早了 {abs_diff} 分钟"
        elif actual_diff > 0:
            return f"晚了 {abs_diff} 分钟"
        else:
            return f"正好等于 {time_type}"


    def _findBestTimeOption(
        self,
        time_options: list,
        target_time: int,
        max_time_diff: int,
        prefer_earlier: bool,
        is_reserve: bool = True
    ) -> tuple:
        """
            Find the best time option from available times.

            Args:
                time_options: List of WebElement time options
                target_time: Target time in minutes
                max_time_diff: Maximum acceptable time difference in minutes
                prefer_earlier: If True, prefer earlier times when diffs are equal
                is_reserve: If True, parse 'time' attribute; if False, parse 'id' attribute

            Returns:
                Tuple of (best_time_element, best_time_text, actual_diff, free_times_list)
                or (None, None, None, []) if no suitable option found
        """
        free_times = []
        best_time_diff = max_time_diff
        best_actual_diff = None
        best_time_opt = None

        for time_opt in time_options:
            # Parse time value based on context
            if is_reserve:
                time_attr = time_opt.get_attribute("time")
                if time_attr == "now":
                    from datetime import datetime
                    now = datetime.now()
                    time_val = now.hour * 60 + now.minute
                elif time_attr and time_attr.isdigit():
                    time_val = int(time_attr)
                else:
                    continue
            else:
                # Renewal context: parse 'id' attribute
                time_attr = time_opt.get_attribute("id")
                if not (time_attr and time_attr.isdigit()):
                    continue
                time_val = int(time_attr)

            free_times.append(time_opt.text.strip() if not is_reserve else self._minsToTime(time_val))

            actual_diff = time_val - target_time
            abs_diff = abs(actual_diff)

            # Update best option if current is better
            if (abs_diff < best_time_diff or
                (abs_diff == best_time_diff and
                 ((prefer_earlier and actual_diff <= 0) or
                  (not prefer_earlier and actual_diff >= 0)))):

                best_time_diff = abs_diff
                best_actual_diff = actual_diff
                best_time_opt = time_opt

        if best_time_opt is not None:
            return (best_time_opt, best_time_opt.text.strip(), best_actual_diff, free_times)
        return (None, None, None, free_times)
