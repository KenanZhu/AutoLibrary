# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import requests

from PySide6.QtCore import (
    QThread,
    Signal
)


class ALBulletinFetchWorker(QThread):
    """
        Worker thread for fetching bulletins from the server.
    """

    fetchWorkerIsFinished = Signal(dict)
    fetchWorkerFinishedWithError = Signal(str)

    def __init__(
        self,
        parent=None,
        request_url: str = "",
        params: dict = None
    ):

        super().__init__(parent)
        self.__request_url = request_url.rstrip("/") if request_url else ""
        self.__params = params or {}

    def run(
        self
    ):

        try:
            response = requests.get(
                self.__request_url, params=self.__params, timeout=5
            )
            response.raise_for_status()
            r = response.json()
            if r.get("code") == 200:
                data = r.get("data", {})
                self.fetchWorkerIsFinished.emit(data)
            else:
                raise Exception(
                    f"服务器返回错误: [{r.get('code', '未知代码')}] {r.get('msg', '未知错误')}"
                )
        except requests.RequestException as e:
            self.fetchWorkerFinishedWithError.emit(f"获取公告数据时发生网络错误: \n{e}")
        except Exception as e:
            self.fetchWorkerFinishedWithError.emit(f"获取公告数据时发生未知错误: \n{e}")
