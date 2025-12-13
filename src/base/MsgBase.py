# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import time
import queue


class MsgBase:

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue
    ):

        self._class_name = self.__class__.__name__
        self._input_queue = input_queue
        self._output_queue = output_queue


    def _showMsg(
        self,
        msg: str
    ):

        self._output_queue.put(f"[{self._class_name:<15}] >>> : {msg}")


    def _showTrace(
        self,
        msg: str
    ):

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self._output_queue.put(f"{timestamp}-[{self._class_name:<15}] : {msg}")


    def _waitMsg(
        self,
        timeout: float = 1.0
    ) -> str:

        try:
            msg = self._input_queue.get(timeout=timeout)
            return msg
        except queue.Empty:
            return None


    def _inputMsg(
        self,
        timeout: float = 1.0
    ) -> bool:

        try:
            self._input_queue.get(timeout=timeout)
            return True
        except queue.Empty:
            return False
