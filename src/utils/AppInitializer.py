# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os

from PySide6.QtCore import QStandardPaths, QDir

from utils.ConfigManager import instance as configInstance
from utils.LogManager import instance as logInstance


def initializeConfigManager(
) -> bool:

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    old_config_dir = os.path.join(app_dir, "config")
    new_config_dir = os.path.join(app_dir, "configs")
    if QDir(old_config_dir).exists(): # old config dir exists
        #we rename it to compatible with new version
        if not QDir().rename(old_config_dir, new_config_dir):
            return False
    elif not QDir(new_config_dir).exists():
        if not QDir().mkpath(new_config_dir):
            return False
    configInstance(new_config_dir)
    return True

def initializeLogManager(
) -> bool:

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    log_dir = os.path.join(app_dir, "logs")
    if not QDir(log_dir).exists():
        if not QDir().mkpath(log_dir):
            return False
    logInstance(log_dir)
    return True

def initializeApp(
) -> bool:

    if not initializeLogManager():
        return False
    if not initializeConfigManager():
        return False
    return True
