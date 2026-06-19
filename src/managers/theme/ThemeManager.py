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
import threading

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QStyleFactory
)

from interfaces.ConfigProvider import CfgKey
from managers.config.ConfigManager import instance as configInstance
from managers.log.LogManager import instance as logInstance
from utils.ThemeUtils import (
    readThemeInfo,
    readThemeQss,
    validateTheme,
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

    def _deleteThemeFile(
        self,
        name: str
    ):
        """
            Delete a theme file in the themes storage directory.

            The caller must hold self.__lock before invoking this method.

            **This method ONLY deletes the file**.
        """

        filepath = os.path.join(self.__themes_dir, name + ".altheme")
        if os.path.isfile(filepath):
            os.remove(filepath)

    def _resolveDestPath(
        self,
        theme_name: str,
        author: str
    ) -> str:
        """
            Resolve the destination path for an imported theme.

            If the default {name}.altheme path does not exist, use it directly.
            If it exists and has a different author, use {name}_{author}.altheme.
            If it exists and has the same author, raise ValueError.

            Args:
                theme_name (str): Sanitised theme name.
                author (str): Theme author string.

            Returns:
                str: The resolved destination file path.

            Raises:
                ValueError: If a theme with the same name and author already exists.
        """

        default_path = os.path.join(self.__themes_dir, theme_name + ".altheme")
        if not os.path.exists(default_path):
            return default_path
        try:
            existing_info = validateTheme(default_path)
            existing_author = existing_info.get("author", "")
        except Exception:
            self._deleteThemeFile(theme_name)  # caller holds the lock
            raise ValueError(
                f"主题 '{theme_name}' 已存在但无法通过验证, 已清理该主题文件"
            )
        if existing_author == author:
            raise ValueError(
                f"主题名称 '{theme_name}' (作者 '{author}') 已存在"
            )
        safe_author = os.path.basename(author) if author else "未知作者"
        alt_path = os.path.join(
            self.__themes_dir, f"{theme_name}_{safe_author}.altheme"
        )
        if os.path.exists(alt_path):
            raise ValueError(
                f"主题名称 '{theme_name}' (作者 '{author}') 已存在"
            )
        return alt_path

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
        base_name, ext = os.path.splitext(os.path.basename(source_path))
        ext = ext.lower()
        with self.__lock:
            if ext == ".qss":
                dest_path = self._resolveDestPath(base_name, "未知作者")
                wrapQssToAtheme(source_path, dest_path, "both")
                return os.path.splitext(os.path.basename(dest_path))[0]
            elif ext == ".altheme":
                info = validateTheme(source_path)
                name = info.get("name", base_name)
                safe_name = os.path.basename(name)
                new_author = info.get("author", "")
                dest_path = self._resolveDestPath(safe_name, new_author)
                shutil.copy2(source_path, dest_path)
                return os.path.splitext(os.path.basename(dest_path))[0]
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
                    info = validateTheme(filepath)
                    name = info.get("name", "")
                    author = info.get("author", "")
                    key = (name, author)
                    if key in seen_keys:
                        logInstance().getLogger("ThemeManager").warning(
                            f"主题名称 '{name}' (作者 '{author}') 重复 (文件 '{filename}') 已跳过"
                        )
                        continue
                    seen_keys.add(key)
                    info["file"] = os.path.splitext(filename)[0]
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
            stylesheet from the application and reverts to the saved
            colour scheme.

            Args:
                name (str): The theme name to remove.
        """

        with self.__lock:
            self._deleteThemeFile(name)
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
            qss = readThemeQss(filepath)
            app = QApplication.instance()
            if app:
                app.setStyleSheet(qss)
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
