# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import re
import time
import queue

from datetime import datetime, timedelta
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from base.LibOperator import LibOperator


class LibCheckout(LibOperator):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        driver: any
    ):

        super().__init__(input_queue, output_queue)

        self.__driver = driver


    def _waitResponseLoad(
        self
    ) -> bool:

        pass