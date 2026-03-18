# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import logging
import os
import threading

from logging.handlers import TimedRotatingFileHandler
from typing import Optional


class CallerInfoFormatter(logging.Formatter):
    """
        Custom formatter to extract real caller information.
        Skips MsgBase._showTrace to show the actual calling location.

        Format:
        - Logger name: left-aligned, max 15 chars
        - Level name: left-aligned, max 8 chars
        - Filename: left-aligned, max 20 chars
        - Line number: left-aligned, max 4 digits
    """

    def __init__(
        self,
        fmt=None,
        datefmt=None,
        style='%'
    ):

        super().__init__(fmt, datefmt, style)
        self.basefmt = fmt

    def format(
        self,
        record
    ):

        depth = 0
        while depth < 10:
            record.filename = os.path.basename(record.pathname)
            if 'MsgBase.py' not in record.filename and record.funcName != '_showTrace':
                break
            if not hasattr(record, 'stack'):
                record.stack = True
                import traceback
                record.stack_list = traceback.extract_stack()
            depth += 1
            if depth < len(record.stack_list):
                frame = record.stack_list[-depth-1]
                record.filename = os.path.basename(frame.filename)
                record.lineno = frame.lineno
                record.funcName = frame.name
        record.name = record.name[-15:].ljust(15)
        record.levelname = record.levelname.ljust(8)
        record.filename = record.filename[-20:].ljust(20)
        record.lineno = f"{record.lineno:04d}"

        return super().format(record)


class LogManager:
    """
        Log Manager Singleton Class

        Args:
            log_dir (str): The directory to store log files.
    """

    def __init__(
        self,
        log_dir: str
    ):

        self.__log_dir = os.path.abspath(log_dir)
        self.__logger = None
        self.__initialized = False

        self.initialize()


    def initialize(
        self
    ):

        if self.__initialized:
            return
        os.makedirs(self.__log_dir, exist_ok=True)
        self.__logger = logging.getLogger("AutoLibrary")
        self.__logger.setLevel(logging.DEBUG)
        self.__logger.handlers.clear()

        formatter = CallerInfoFormatter(
            '[%(asctime)s] - [%(name)s] - [%(levelname)s] - [%(filename)s:%(lineno)s] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.__logger.addHandler(console_handler)

        all_log_file = os.path.join(self.__log_dir, "all.log")
        file_handler_all = TimedRotatingFileHandler(
            all_log_file,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler_all.suffix = "%Y-%m-%d.log"
        file_handler_all.setLevel(logging.DEBUG)
        file_handler_all.setFormatter(formatter)
        self.__logger.addHandler(file_handler_all)

        error_log_file = os.path.join(self.__log_dir, "error.log")
        file_handler_error = TimedRotatingFileHandler(
            error_log_file,
            when='midnight',
            interval=1,
            backupCount=14,
            encoding='utf-8'
        )
        file_handler_error.suffix = "%Y-%m-%d.log"
        file_handler_error.setLevel(logging.ERROR)
        file_handler_error.setFormatter(formatter)
        self.__logger.addHandler(file_handler_error)

        self.__initialized = True


    def getLogger(
        self,
        name: Optional[str] = None
    ) -> logging.Logger:

        if name:
            return self.__logger.getChild(name)
        return self.__logger


    def setLevel(
        self,
        level: int
    ):

        if self.__logger:
            self.__logger.setLevel(level)


    def logDir(
        self
    ) -> str:

        return self.__log_dir


# LogManager singleton instance.
_log_manager_instance = None

# Singleton instance lock.
_instance_lock = threading.Lock()
def instance(
    log_dir: str = ""
) -> LogManager:

    global _log_manager_instance
    with _instance_lock:
        if _log_manager_instance is None:
            if not log_dir:
                raise ValueError("LogManager initialization requires log_dir parameter")
            _log_manager_instance = LogManager(log_dir)
        else:
            if log_dir and _log_manager_instance.logDir() != os.path.abspath(log_dir):
                raise ValueError("LogManager instance already initialized with a different log directory")
    return _log_manager_instance


def getLogger(
    name: Optional[str] = None
) -> logging.Logger:

    if _log_manager_instance is None:
        raise RuntimeError("LogManager not initialized, please call LogManager.instance(log_dir) first")
    return _log_manager_instance.getLogger(name)
