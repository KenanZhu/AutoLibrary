# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue
import re
import time
from datetime import datetime, timedelta

from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)

from base.MsgBase import MsgBase
from pages.MainShell import MainShell
from pages.RecordsView import RecordsView


class RecordChecker(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
    ) -> None:

        super().__init__(input_queue, output_queue)

    @staticmethod
    def _formatDiffTime(
        seconds: float,
    ) -> str:

        hours = int(seconds // 3600)
        minutes = int(seconds % 3600 // 60)
        seconds = int(seconds % 60)
        return f"{hours} 时 {minutes} 分 {seconds} 秒"

    def _getReserveRecord(
        self,
        shell: MainShell,
        wanted_date: str,
        wanted_status: str,
    ) -> dict | None:

        if wanted_date is None:
            self._showTrace("日期未指定, 无法检查当前预约状态", self.TraceLevel.WARNING)
            return None
        self._showTrace(
            f"正在检查用户在 {wanted_date} 是否有预约状态为 "
            f"{wanted_status} 的预约记录......", 20, no_log=True
        )

        checked_count = 0
        max_check_times = 6

        records_view = shell.gotoRecordsView()
        for _ in range(max_check_times):
            reservations = records_view.loadRecords()
            if reservations is None:
                return None
            for reservation in reservations[checked_count:]:
                record = self._decodeReserveRecord(reservation, records_view)
                checked_count += 1
                if record is None:
                    continue
                if record["date"] == "":
                    continue
                if record["time"] == {"begin": "", "end": ""}:
                    continue
                if (
                    datetime.strptime(record["date"], "%Y-%m-%d").date()
                    > datetime.strptime(wanted_date, "%Y-%m-%d").date()
                ):
                    continue
                if (
                    datetime.strptime(record["date"], "%Y-%m-%d").date()
                    < datetime.strptime(wanted_date, "%Y-%m-%d").date()
                ):
                    return None
                if record["info"]["status"] == wanted_status:
                    self._showTrace(
                        f"寻找到用户第 {checked_count} 条状态为 "
                        f"{wanted_status} 的预约记录, "
                        f"详细信息: {record['date']} "
                        f"{record['time']['begin']} - "
                        f"{record['time']['end']} "
                        f"{record['info']['location']}",
                        20, no_log=True,
                    )
                    return record
            if not records_view.showMoreRecords():
                break
        return None

    def _decodeReserveRecord(
        self,
        reservation,
        records_view: RecordsView,
    ) -> dict:

        try:
            time_element = records_view.getRecordTimeElement(reservation)
            info_elements = records_view.getRecordInfoElements(reservation)
        except (NoSuchElementException, TimeoutException, StaleElementReferenceException):
            return {
                "date": "",
                "time": {"begin": "", "end": ""},
                "info": {"location": "", "status": ""},
            }
        except Exception:
            return {
                "date": "",
                "time": {"begin": "", "end": ""},
                "info": {"location": "", "status": ""},
            }
        time_data = self._decodeReserveTime(time_element)
        info_data = self._decodeReserveInfo(info_elements)
        return {
            "date": time_data["date"],
            "time": time_data["time"],
            "info": info_data,
        }

    def _decodeReserveTime(
        self,
        time_element,
    ) -> dict:

        time_str = time_element.text.strip()
        today = datetime.now().date()
        if "明天" in time_str:
            target_date = today + timedelta(days=1)
            date = target_date.strftime("%Y-%m-%d")
        elif "今天" in time_str:
            target_date = today
            date = target_date.strftime("%Y-%m-%d")
        elif "昨天" in time_str:
            target_date = today - timedelta(days=1)
            date = target_date.strftime("%Y-%m-%d")
        else:
            date_match = re.search(r"(\d{4}-\d{1,2}-\d{1,2})", time_str)
            if date_match:
                date = date_match.group(1)
            else:
                date = ""
        time_match = re.search(
            r"(\d{1,2}:\d{2}) -- (\d{1,2}:\d{2})", time_str
        )
        if time_match:
            begin_time = time_match.group(1)
            end_time = time_match.group(2)
        else:
            begin_time = ""
            end_time = ""
        return {
            "date": date,
            "time": {"begin": begin_time, "end": end_time},
        }

    def _decodeReserveInfo(
        self,
        info_elements,
    ) -> dict:

        location = ""
        status = ""
        for info in info_elements:
            if "已预约" in info.text:
                status = "已预约"
            elif "使用中" in info.text:
                status = "使用中"
            elif "已完成" in info.text:
                status = "已完成"
            elif "已结束使用" in info.text:
                status = "已结束使用"
            elif "已取消" in info.text:
                status = "已取消"
            elif "失约" in info.text:
                status = "失约"
            elif "图书馆" in info.text:
                location = info.text.strip()
        return {"location": location, "status": status}

    def canReserve(
        self,
        shell: MainShell,
        date: str,
    ) -> bool:

        if self._getReserveRecord(shell, date, "已预约") is None:
            if self._getReserveRecord(shell, date, "使用中") is None:
                self._showTrace(f"用户在 {date} 可以预约")
                return True
            self._showTrace(f"用户在 {date} 有使用中的预约, 无法预约")
            return False
        self._showTrace(f"用户在 {date} 已存在有效预约, 无法预约")
        return False

    def canCheckin(
        self,
        shell: MainShell,
    ) -> bool:

        date = time.strftime("%Y-%m-%d", time.localtime())
        record = self._getReserveRecord(shell, date, "已预约")
        if record is not None:
            begin_time = record["time"]["begin"]
            begin_time = datetime.strptime(
                f"{date} {begin_time}", "%Y-%m-%d %H:%M"
            )
            time_diff = datetime.now() - begin_time
            time_diff_seconds = time_diff.total_seconds()
            if time_diff_seconds < -30 * 60:
                self._showTrace(
                    f"用户在 {date} 的预约开始时间为 {begin_time}, "
                    f"当前距离预约开始时间还有 "
                    f"{self._formatDiffTime(abs(time_diff_seconds))}, 无法签到"
                )
                return False
            elif -30 * 60 <= time_diff_seconds < 0:
                self._showTrace(
                    f"用户在 {date} 的预约开始时间为 {begin_time}, "
                    f"当前距离预约开始时间还有 "
                    f"{self._formatDiffTime(abs(time_diff_seconds))}, 可以签到"
                )
                return True
            elif 0 <= time_diff_seconds < 30 * 60 - 5:
                self._showTrace(
                    f"用户在 {date} 的预约开始时间为 {begin_time}, "
                    f"当前距离预约开始时间已经过去 "
                    f"{self._formatDiffTime(abs(time_diff_seconds))}, 可以签到"
                )
                return True
        self._showTrace(f"用户在 {date} 没有有效预约记录, 无法签到")
        return False

    def canRenew(
        self,
        shell: MainShell,
    ) -> tuple[bool, dict]:

        date = time.strftime("%Y-%m-%d", time.localtime())
        record = self._getReserveRecord(shell, date, "使用中")
        if record is not None:
            end_time = record["time"]["end"]
            end_time = datetime.strptime(
                f"{date} {end_time}", "%Y-%m-%d %H:%M"
            )
            time_diff = end_time - datetime.now()
            time_diff_seconds = time_diff.total_seconds()
            trace_msg = (
                f"用户在 {date} 的预约结束时间为 {end_time}, "
                f"当前距离预约结束时间还有 "
                f"{self._formatDiffTime(abs(time_diff_seconds))}"
            )
            if abs(time_diff_seconds) < 120 * 60:
                self._showTrace(f"{trace_msg}, 可以续约")
                return True, record
            else:
                self._showTrace(f"{trace_msg}, 无法续约")
                return False, None
        self._showTrace(f"用户在 {date} 没有有效预约记录, 无法续约")
        return False, None

    def postRenewCheck(
        self,
        shell: MainShell,
        record: dict,
    ) -> bool:

        date = record["date"]
        act_record = self._getReserveRecord(shell, date, "使用中")
        if act_record is not None:
            if (
                act_record["time"]["begin"] == record["time"]["begin"]
                and act_record["time"]["end"] == record["time"]["end"]
            ):
                self._showTrace(
                    f"\n"
                    f"      续约成功 !\n"
                    f"          日 期 ：{date}\n"
                    f"          时 间 ：{act_record['time']['begin']}"
                    f" - {act_record['time']['end']}\n"
                    f"          位 置 ：{act_record['info']['location']}\n"
                    f"          状 态 ：{act_record['info']['status']}"
                )
                return True
            else:
                self._showTrace(
                    f"\n"
                    f"      续约失败 !\n"
                    f"          续约后结束时间为 {act_record['time']['end']},"
                    f"与预期结束时间 {record['time']['end']} 不符 !"
                )
                return False
        self._showTrace(f"用户在 {date} 没有有效预约记录, 无法检查续约结果")
        return False
