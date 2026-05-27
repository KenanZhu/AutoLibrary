# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Callable, Optional

from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from pages.components.Dialog import Dialog
from pages.strategies.TimeSelectMaker import (
    TimeRangeResult,
    TimeSelectionResult,
    TimeSelectMaker,
    minsToTimeStr,
    timeStrToMins,
)

if TYPE_CHECKING:
    from pages.flows.ReserveFlow import ReserveContext


class TimeSelectDialog(Dialog):
    """
        Time selection panel that appears after selecting a seat.

        Contains start-time and end-time option lists.
        Does NOT auto-close — the reserve submission handles cleanup.
    """

    ROOT = (By.CSS_SELECTOR, "#startTime ul")

    def __init__(
        self,
        driver: WebDriver,
        tracer: Optional[Callable[[str, int], None]] = None,
    ) -> None:

        super().__init__(driver, self.ROOT, auto_close_on_exit=False)
        self._tracer = tracer

    def _trace(
        self,
        msg: str,
        level: int = logging.INFO,
    ) -> None:

        if self._tracer is not None:
            self._tracer(msg, level)

    def _logTimeStep(
        self,
        time_type: str,
        target_mins: int,
        max_diff: int,
        step_result: TimeSelectionResult,
    ) -> bool:

        if step_result.selected_index >= 0:
            abs_diff = abs(step_result.actual_diff)
            if step_result.actual_diff < 0:
                relation = f"早了 {abs_diff} 分钟"
            elif step_result.actual_diff > 0:
                relation = f"晚了 {abs_diff} 分钟"
            else:
                relation = f"正好等于 {time_type}"
            self._trace(
                f"选择距离期望 {time_type} 最近的 {step_result.display_text}, "
                f"与期望 {time_type} 相比 {relation}"
            )
            return True
        if not step_result.free_times:
            self._trace(
                f"{time_type} 选择失败 ! : 当前未查询到可用时间",
                logging.ERROR,
            )
        else:
            target_str = minsToTimeStr(target_mins)
            self._trace(
                f"无法选择最近的 {time_type} {target_str}, "
                f"所有可选时间与目标时间相差都超过 {max_diff} 分钟",
                logging.WARNING,
            )
            self._trace(f"当前可供预约的 {time_type} 有: {step_result.free_times}")
        return False

    def getTimeOptions(
        self,
        time_id: str,
    ) -> list[WebElement]:

        try:
            self._waitAllPresence(
                (By.CSS_SELECTOR, f"#{time_id} ul li a")
            )
        except (NoSuchElementException, TimeoutException):
            return []
        except Exception:
            return []
        return self._findAll(
            By.CSS_SELECTOR,
            f"#{time_id} ul li a",
        )

    def selectNearestTime(
        self,
        time_id: str,
        target_time: int,
        max_time_diff: int,
        prefer_earlier: bool,
    ) -> TimeSelectionResult:

        all_time_opts = self.getTimeOptions(time_id)
        if not all_time_opts:
            return TimeSelectionResult()
        result = TimeSelectMaker.forReserve().decide(
            all_time_opts,
            target_time,
            max_time_diff,
            prefer_earlier,
        )
        if result.selected_index >= 0:
            all_time_opts[result.selected_index].click()
        return result

    def selectTimeRange(
        self,
        begin_target: int,
        end_target: int,
        begin_max_diff: int = 30,
        end_max_diff: int = 30,
        begin_prefer_early: bool = True,
        end_prefer_early: bool = False,
        satisfy_duration: bool = True,
        expect_duration: int = 4,
        library_close_mins: int = TimeSelectMaker.LIBRARY_CLOSE_MINS,
    ) -> TimeRangeResult:

        begin_result = self.selectNearestTime(
            "startTime",
            begin_target,
            begin_max_diff,
            begin_prefer_early,
        )
        if begin_result.selected_index < 0:
            return TimeRangeResult(begin_result=begin_result)
        actual_begin = begin_result.selected_value
        if satisfy_duration:
            end_target = TimeSelectMaker.calcEndTime(
                actual_begin,
                expect_duration,
                library_close_mins,
            )
        end_result = self.selectNearestTime(
            "endTime",
            end_target,
            end_max_diff,
            end_prefer_early,
        )
        if end_result.selected_index < 0:
            return TimeRangeResult(
                begin_result=begin_result,
                actual_begin_mins=actual_begin,
                end_result=end_result,
                expect_end_mins=end_target,
            )
        return TimeRangeResult(
            begin_result=begin_result,
            end_result=end_result,
            actual_begin_mins=actual_begin,
            actual_end_mins=end_result.selected_value,
            expect_end_mins=end_target,
        )

    def selectSeatTime(
        self,
        ctx: ReserveContext,
        library_close_mins: int = TimeSelectMaker.LIBRARY_CLOSE_MINS,
    ) -> bool:

        exp_beg_mins = timeStrToMins(ctx.begin_time)
        exp_end_mins = timeStrToMins(ctx.end_time)
        result = self.selectTimeRange(
            begin_target=exp_beg_mins,
            end_target=exp_end_mins,
            begin_max_diff=ctx.begin_max_diff,
            end_max_diff=ctx.end_max_diff,
            begin_prefer_early=ctx.begin_prefer_early,
            end_prefer_early=ctx.end_prefer_early,
            satisfy_duration=ctx.satisfy_duration,
            expect_duration=ctx.expect_duration,
            library_close_mins=library_close_mins,
        )
        if not self._logTimeStep("开始时间", exp_beg_mins, ctx.begin_max_diff, result.begin_result):
            return False
        if ctx.satisfy_duration:
            unclipped = result.actual_begin_mins + ctx.expect_duration*60
            if unclipped > library_close_mins:
                self._trace(
                    f"预约持续时间 {ctx.expect_duration} 小时, 超过最大预约时间 {minsToTimeStr(library_close_mins)}, "
                    f"自动调整为 {minsToTimeStr(library_close_mins)}",
                    logging.WARNING,
                )
            act_beg_str = minsToTimeStr(result.actual_begin_mins)
            exp_end_str = minsToTimeStr(result.expect_end_mins)
            self._trace(
                f"需要满足期望预约持续时间: {ctx.expect_duration} 小时, "
                f"根据开始时间 {act_beg_str} 计算结束时间: {exp_end_str}"
            )
        if not self._logTimeStep("结束时间", result.expect_end_mins, ctx.end_max_diff, result.end_result):
            return False
        act_beg_str = minsToTimeStr(result.actual_begin_mins)
        act_end_str = minsToTimeStr(result.actual_end_mins)
        exp_end_str = minsToTimeStr(result.expect_end_mins)
        self._trace(
            f"期望预约时间段: {ctx.begin_time} - {exp_end_str}, "
            f"实际预约时间段: {act_beg_str} - {act_end_str}"
        )
        return True
