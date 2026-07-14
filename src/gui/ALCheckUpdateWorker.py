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


class ALCheckUpdateWorker(QThread):
    """
        Worker thread for checking latest release from GitHub API.
    """

    checkUpdateWorkerIsFinished = Signal(dict)
    checkUpdateWorkerFinishedWithError = Signal(str)

    def __init__(
        self,
        parent=None
    ):

        super().__init__(parent)
        self.__api_url = "https://api.github.com/repos/KenanZhu/AutoLibrary/releases/latest"

    def run(
        self
    ):

        try:
            response = requests.get(self.__api_url, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.checkUpdateWorkerIsFinished.emit({
                "tag_name": data.get("tag_name", ""),
                "name": data.get("name", ""),
                "html_url": data.get("html_url", ""),
                "body": data.get("body", ""),
            })
        except requests.RequestException as e:
            self.checkUpdateWorkerFinishedWithError.emit(f"网络请求失败: \n{e}")
        except Exception as e:
            self.checkUpdateWorkerFinishedWithError.emit(f"检查更新时发生未知错误: \n{e}")
