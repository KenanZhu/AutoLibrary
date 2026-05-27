# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from pages.flows._helpers import minsToTimeStr


@dataclass
class TimeOption:

    value: int
    element_text: str


@dataclass
class TimeSelectionResult:

    selected_index: int = -1
    selected_value: int = 0
    display_text: str = ""
    actual_diff: int = 0
    free_times: list[str] = field(default_factory=list)


class TimeOptionReader(ABC):

    @abstractmethod
    def readOptions(
        self,
        elements: list,
    ) -> list[TimeOption]:
        ...

    def formatFreeTime(
        self,
        opt: TimeOption,
    ) -> str:

        return opt.element_text


class ReserveTimeReader(TimeOptionReader):
    """
        Reads the ``time`` HTML attribute for the reserve flow.
        Special value ``"now"`` is resolved to the current wall-clock minute.
    """

    def readOptions(
        self,
        elements: list,
    ) -> list[TimeOption]:

        options: list[TimeOption] = []
        for el in elements:
            time_attr = el.get_attribute("time")
            if time_attr == "now":
                now = datetime.now()
                value = now.hour * 60 + now.minute
            elif time_attr and time_attr.isdigit():
                value = int(time_attr)
            else:
                continue
            options.append(TimeOption(value=value, element_text=el.text.strip()))
        return options

    def formatFreeTime(
        self,
        opt: TimeOption,
    ) -> str:

        return minsToTimeStr(opt.value)


class RenewTimeReader(TimeOptionReader):
    """
        Reads the ``id`` HTML attribute for the renewal flow.
    """

    def readOptions(
        self,
        elements: list,
    ) -> list[TimeOption]:

        options: list[TimeOption] = []
        for el in elements:
            time_attr = el.get_attribute("id")
            if not (time_attr and time_attr.isdigit()):
                continue
            options.append(TimeOption(value=int(time_attr), element_text=el.text.strip()))
        return options


class TimeDecisionMaker:

    def __init__(
        self,
        reader: TimeOptionReader,
    ) -> None:

        self._reader = reader

    def decide(
        self,
        elements: list,
        target_time: int,
        max_time_diff: int,
        prefer_earlier: bool,
    ) -> TimeSelectionResult:

        options = self._reader.readOptions(elements)
        free_times = [self._reader.formatFreeTime(o) for o in options]
        best_diff = max_time_diff
        best_actual_diff = None
        best_index = -1
        for i, opt in enumerate(options):
            actual_diff = opt.value - target_time
            abs_diff = abs(actual_diff)
            if abs_diff < best_diff or (
                abs_diff == best_diff
                and (
                    (prefer_earlier and actual_diff <= 0)
                    or (not prefer_earlier and actual_diff >= 0)
                )
            ):
                best_diff = abs_diff
                best_actual_diff = actual_diff
                best_index = i
        if best_index == -1:
            return TimeSelectionResult(free_times=free_times)
        chosen = options[best_index]
        return TimeSelectionResult(
            selected_index=best_index,
            selected_value=chosen.value,
            display_text=chosen.element_text,
            actual_diff=best_actual_diff or 0,
            free_times=free_times,
        )


class TimeSelectMaker:

    LIBRARY_CLOSE_MINS = 1410
    MAX_DURATION_HOURS = 8

    @staticmethod
    def forReserve(
    ) -> TimeDecisionMaker:

        return TimeDecisionMaker(ReserveTimeReader())

    @staticmethod
    def forRenew(
    ) -> TimeDecisionMaker:

        return TimeDecisionMaker(RenewTimeReader())
