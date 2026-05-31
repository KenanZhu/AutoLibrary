# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import shutil
import tempfile
import threading
import zipfile

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QStyleFactory
)

from interfaces.ConfigProvider import CfgKey
from managers.config.ConfigManager import instance as configInstance
from managers.log.LogManager import instance as logInstance
from utils.ThemeUtils import (
    packTheme,
    readThemeInfo,
    unpackTheme,
    wrapQssToAtheme
)


_active_style_name = "Fusion"


def setActiveStyle(
    style_name: str
):

    global _active_style_name
    _active_style_name = style_name

def getActiveStyle(
) -> str:

    return _active_style_name


class ThemeManager:
    """
        Theme manager class.

        Manages the themes storage directory, providing import,
        list, remove, and apply operations for .altheme theme files.

        Args:
            themes_dir (str): Path to the themes storage directory.
    """

    def __init__(
        self,
        themes_dir: str
    ):

        self.__themes_dir = os.path.abspath(themes_dir)
        self.__lock = threading.Lock()
        self.__current_theme_name = ""
        os.makedirs(self.__themes_dir, exist_ok=True)

    @staticmethod
    def _colorSchemeFor(
        theme: str
    ) -> Qt.ColorScheme:
        """
            Map a theme identifier to the corresponding Qt color scheme.
        """

        if theme == "dark":
            return Qt.ColorScheme.Dark
        elif theme == "light":
            return Qt.ColorScheme.Light
        else:
            return Qt.ColorScheme.Unknown

    def themesDir(
        self
    ) -> str:
        """
            Get the themes directory path.

            Returns:
                str: The absolute path to the themes storage directory.
        """

        return self.__themes_dir

    def importTheme(
        self,
        source_path: str
    ) -> str:
        """
            Import a theme file into the themes directory.

            Supports .altheme (zip archive) and bare .qss files.
            Bare .qss files are automatically wrapped into .altheme format.
            For .altheme files, validates that theme.qss exists in the archive
            and sanitises the theme name to prevent path traversal.

            Args:
                source_path (str): Path to the .altheme or .qss file.

            Returns:
                str: The imported theme name.

            Raises:
                FileNotFoundError: If source_path does not exist.
                ValueError: If the file type is unsupported or the .altheme is invalid.
        """

        if not os.path.isfile(source_path):
            raise FileNotFoundError(source_path)
        ext = os.path.splitext(source_path)[1].lower()
        with self.__lock:
            if ext == ".qss":
                name = os.path.splitext(os.path.basename(source_path))[0]
                dest_path = os.path.join(self.__themes_dir, name + ".altheme")
                if os.path.exists(dest_path):
                    raise ValueError(f"主题 '{name}' 已存在")
                wrapQssToAtheme(source_path, dest_path, "both")
                return name
            elif ext == ".altheme":
                with zipfile.ZipFile(source_path, "r") as zf:
                    if "theme.qss" not in zf.namelist():
                        raise ValueError("无效的 .altheme: 缺少 theme.qss")
                info = readThemeInfo(source_path)
                name = info.get("name", os.path.splitext(os.path.basename(source_path))[0])
                safe_name = os.path.basename(name)
                dest_path = os.path.join(self.__themes_dir, safe_name + ".altheme")
                if os.path.exists(dest_path):
                    raise ValueError(f"主题 '{safe_name}' 已存在")
                # Check for name collision with existing themes by the same author
                new_author = info.get("author", "")
                for existing in self.listThemes():
                    if (existing.get("name", "") == safe_name
                        and existing.get("author", "") == new_author):
                        raise ValueError(
                            f"主题名称 '{safe_name}' (作者 '{new_author}') 已存在"
                        )
                shutil.copy2(source_path, dest_path)
                return safe_name
            else:
                raise ValueError(f"不支持的文件类型: {ext}")

    def listThemes(
        self
    ) -> list:
        """
            List all available themes in the themes directory.

            Scans the themes directory for .altheme files and reads
            their info.json metadata.

            Returns:
                list[dict]: A list of theme info dictionaries.
        """

        themes = []
        seen_keys = set()
        if not os.path.isdir(self.__themes_dir):
            return themes
        for filename in sorted(os.listdir(self.__themes_dir)):
            if filename.endswith(".altheme"):
                filepath = os.path.join(self.__themes_dir, filename)
                try:
                    info = readThemeInfo(filepath)
                    with zipfile.ZipFile(filepath, "r") as zf:
                        if "theme.qss" not in zf.namelist():
                            raise ValueError("缺少 theme.qss")
                    name = info.get("name", "")
                    author = info.get("author", "")
                    key = (name, author)
                    if key in seen_keys:
                        logInstance().getLogger("ThemeManager").warning(
                            f"主题名称 '{name}' (作者 '{author}') 重复 (文件 '{filename}') 已跳过"
                        )
                        continue
                    seen_keys.add(key)
                    themes.append(info)
                except Exception as e:
                    logInstance().getLogger("ThemeManager").warning(
                        f"无法读取主题文件 '{filename}'，已跳过: {e}"
                    )
            else:
                logInstance().getLogger("ThemeManager").warning(
                    f"未知文件类型 '{filename}'，已跳过"
                )
        return themes

    def removeTheme(
        self,
        name: str
    ):
        """
            Remove a theme by name.

            If the removed theme is currently active, clears the QSS
            stylesheet from the application.

            Args:
                name (str): The theme name to remove.
        """

        filepath = os.path.join(self.__themes_dir, name + ".altheme")
        with self.__lock:
            if os.path.isfile(filepath):
                os.remove(filepath)
                if self.__current_theme_name == name:
                    self.__current_theme_name = ""
                    saved_theme = configInstance().get(
                        CfgKey.GLOBAL.APPEARANCE.THEME, "system"
                    )
                    self.clearTheme(saved_theme)

    def applyTheme(
        self,
        name: str
    ):
        """
            Apply a theme by name.

            Extracts the QSS from the .altheme file, applies it to
            QApplication, and sets the Qt color scheme based on
            the theme's need_theme metadata.

            Args:
                name (str): The theme name to apply.

            Raises:
                FileNotFoundError: If the theme .altheme file does not exist.
        """

        filepath = os.path.join(self.__themes_dir, name + ".altheme")
        if not os.path.isfile(filepath):
            raise FileNotFoundError(filepath)
        with self.__lock:
            info = readThemeInfo(filepath)
            with tempfile.TemporaryDirectory() as tmpdir:
                unpackTheme(filepath, tmpdir)
                qss_path = os.path.join(tmpdir, "theme.qss")
                if os.path.isfile(qss_path):
                    with open(qss_path, "r", encoding="utf-8") as fh:
                        qss = fh.read()
                    app = QApplication.instance()
                    if app:
                        app.setStyleSheet(qss)
                else:
                    raise ValueError(
                        f"主题 '{name}' 的 .altheme 文件中缺少 theme.qss"
                    )
            app = QApplication.instance()
            if app:
                need_theme = info.get("need_theme", "both")
                app.styleHints().setColorScheme(
                    ThemeManager._colorSchemeFor(need_theme)
                )
                app.setStyle(QStyleFactory.create(_active_style_name))
            self.__current_theme_name = name

    def clearTheme(
        self,
        theme: str
    ):
        """
            Clear the current QSS stylesheet and apply the given color scheme.

            Args:
                theme (str): The color scheme to apply after clearing
                             ("light", "dark", or "system").
        """

        app = QApplication.instance()
        if not app:
            return
        app.setStyleSheet("")
        app.styleHints().setColorScheme(
            ThemeManager._colorSchemeFor(theme)
        )
        app.setStyle(QStyleFactory.create(_active_style_name))


# ThemeManager singleton instance.
_theme_manager_instance = None

# Singleton instance lock.
_instance_lock = threading.Lock()


def instance(
    themes_dir: str = ""
) -> ThemeManager:
    """
        Get the ThemeManager singleton instance.

        On first call, initialises the ThemeManager with the themes
        directory derived from ConfigManager's config directory.

        Args:
            themes_dir (str): Optional themes directory path.

        Returns:
            ThemeManager: The singleton ThemeManager instance.
    """

    global _theme_manager_instance
    with _instance_lock:
        if _theme_manager_instance is None:
            if not themes_dir:
                cfg = configInstance()
                themes_dir = os.path.join(cfg.configDir(), "themes")
            _theme_manager_instance = ThemeManager(themes_dir)
    return _theme_manager_instance
