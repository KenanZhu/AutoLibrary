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
from PySide6.QtWidgets import QApplication

from managers.config.ConfigManager import instance as configInstance
from utils.ThemeUtils import (
    packTheme,
    readThemeInfo,
    unpackTheme,
    wrapQssToAtheme
)


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
        if not os.path.isdir(self.__themes_dir):
            return themes
        for filename in sorted(os.listdir(self.__themes_dir)):
            if filename.endswith(".altheme"):
                filepath = os.path.join(self.__themes_dir, filename)
                try:
                    info = readThemeInfo(filepath)
                    themes.append(info)
                except Exception:
                    pass
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
                    self._clearQss()

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
            app = QApplication.instance()
            if app:
                need_theme = info.get("need_theme", "both")
                if need_theme == "dark":
                    app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
                elif need_theme == "light":
                    app.styleHints().setColorScheme(Qt.ColorScheme.Light)
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
        if app:
            app.setStyleSheet("")
        self._applyColorScheme(theme)

    def applyThemeOrClear(
        self,
        name: str,
        fallback_theme: str = "system"
    ):
        """
            Apply a custom theme by name, or clear to fallback if empty.

            Args:
                name (str): The theme name to apply, or empty to clear.
                fallback_theme (str): Color scheme to use if name is empty
                                      or if the theme fails to apply.
        """

        if not name:
            self.clearTheme(fallback_theme)
            return
        try:
            self.applyTheme(name)
        except Exception:
            self.clearTheme(fallback_theme)

    def _applyColorScheme(
        self,
        theme: str
    ):
        """
            Set the Qt application color scheme.

            Args:
                theme (str): "dark", "light", or any other value for system default.
        """

        app = QApplication.instance()
        if not app:
            return
        if theme == "dark":
            app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
        elif theme == "light":
            app.styleHints().setColorScheme(Qt.ColorScheme.Light)
        else:
            app.styleHints().setColorScheme(Qt.ColorScheme.Unknown)

    @staticmethod
    def themeToReadable(
        need_theme: str
    ) -> str:
        """
            Convert a need_theme code to human-readable Chinese text.

            Args:
                need_theme (str): "dark", "light", "both", or other.

            Returns:
                str: Readable Chinese label.
        """

        if need_theme == "dark":
            return "深色"
        elif need_theme == "light":
            return "浅色"
        elif need_theme == "both":
            return "所有"
        else:
            return "未知"

    def currentThemeName(
        self
    ) -> str:
        """
            Get the name of the currently active theme.

            Returns:
                str: Current theme name, or empty string if none is active.
        """

        return self.__current_theme_name

    def _clearQss(
        self
    ):
        """
            Clear the current QSS stylesheet from the application.
        """

        app = QApplication.instance()
        if app:
            app.setStyleSheet("")

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
