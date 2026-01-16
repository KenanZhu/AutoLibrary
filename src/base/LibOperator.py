# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import queue

from base.MsgBase import MsgBase


class LibOperator(MsgBase):
    """
        Base abstract class for library operation.

        This class provides the foundation for library-related operations, inheriting
        message handling and tracing abilities from MsgBase. It serves as an abstract
        base class that must be subclassed to implement specific library functionality.
    """

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
