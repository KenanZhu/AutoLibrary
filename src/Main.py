# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import sys

from PySide6.QtCore import QTranslator, QStandardPaths, QDir
from PySide6.QtWidgets import QApplication

from gui.ALMainWindow import ALMainWindow
from gui.resources import ALResource

from utils.ConfigManager import instance as configInstance
from utils.LogManager import instance as logInstance


def initializeConfigManager():

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    config_dir = os.path.join(app_dir, "config")
    if not QDir(config_dir).exists():
        QDir().mkpath(config_dir)
    configInstance(config_dir)

def initializeLogManager():

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    log_dir = os.path.join(app_dir, "logs")
    if not QDir(log_dir).exists():
        QDir().mkpath(log_dir)
    logInstance(log_dir)

def main():

    app = QApplication(sys.argv)
    translator = QTranslator()
    if translator.load(":/res/trans/translators/qtbase_zh_CN.ts"):
        app.installTranslator(translator)
    app.setStyle('Fusion')
    app.setApplicationName("AutoLibrary")
    initializeConfigManager()
    initializeLogManager()
    window = ALMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":

    main()