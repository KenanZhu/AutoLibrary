# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from base.MsgBase import MsgBase


class LibOperator(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue
    ):

        super().__init__(input_queue, output_queue)


    def _waitResponseLoad(
        self
    ) -> bool:

        pass
