# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os

from PySide6.QtCore import QStandardPaths, QDir
from PySide6.QtWidgets import QApplication

from gui.ALSettingsWidget import _applyTheme
from interfaces.ConfigProvider import CfgKey
from managers.config.ConfigManager import instance as configInstance
from managers.driver.WebDriverManager import instance as webdriverInstance
from managers.log.LogManager import instance as logInstance


def _initializeLogManager(
) -> bool:

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    log_dir = os.path.join(app_dir, "logs")
    if not QDir(log_dir).exists():
        if not QDir().mkpath(log_dir):
            return False
    logInstance(log_dir)
    return True

def _initializeConfigManager(
) -> bool:

    logger = logInstance().getLogger("AppInitializer")

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    old_config_dir = os.path.join(app_dir, "config")
    new_config_dir = os.path.join(app_dir, "configs")
    if QDir(old_config_dir).exists(): # old config dir exists
        #we rename it to compatible with new version
        logger.info("存在旧配置目录 %s,将其重命名为 %s", old_config_dir, new_config_dir)
        if not QDir().rename(old_config_dir, new_config_dir):
            logger.error("重命名旧配置目录 %s 到 %s 失败", old_config_dir, new_config_dir)
            return False
    elif not QDir(new_config_dir).exists():
        logger.info("初始化配置目录 %s", new_config_dir)
        if not QDir().mkpath(new_config_dir):
            logger.error("创建配置目录 %s 失败", new_config_dir)
            return False
    configInstance(new_config_dir)
    return True

def _initializeWebDriverManager(
) -> bool:

    logger = logInstance().getLogger("AppInitializer")

    app_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    driver_dir = os.path.join(app_dir, "drivers")
    if not QDir(driver_dir).exists():
        logger.info("初始化驱动目录 %s", driver_dir)
        if not QDir().mkpath(driver_dir):
            logger.error("创建驱动目录 %s 失败", driver_dir)
            return False
    webdriverInstance(driver_dir)
    return True

def _initializeAppearance(
):

    app = QApplication.instance()
    if not app:
        return
    cfg = configInstance()
    saved_style = cfg.get(CfgKey.GLOBAL.APPEARANCE.STYLE, "Fusion")
    saved_theme = cfg.get(CfgKey.GLOBAL.APPEARANCE.THEME, "system")
    app.setStyle(saved_style)
    _applyTheme(saved_theme)

def initializeApp(
) -> bool:
    """
        Initialize the application components

        Order:
            LogManager -> ConfigManager -> WebDriverManager -> Appearance
    """

    if not _initializeLogManager():
        return False
    if not _initializeConfigManager():
        return False
    if not _initializeWebDriverManager():
        return False
    _initializeAppearance()
    return True
