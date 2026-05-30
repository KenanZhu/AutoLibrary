# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import json
import os
import zipfile


def packTheme(
    qss_path: str,
    info: dict,
    output_path: str
):
    """
        Pack a .qss file and info dict into a .altheme file.

        The .altheme file is a zip archive containing info.json and theme.qss.

        Args:
            qss_path (str): Path to the .qss stylesheet file.
            info (dict): Theme metadata dict with keys name, author, need_theme, brief.
            output_path (str): Destination path for the .altheme file.

        Raises:
            FileNotFoundError: If qss_path does not exist.
    """

    if not os.path.isfile(qss_path):
        raise FileNotFoundError(qss_path)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("info.json", json.dumps(info, ensure_ascii=False, indent=4))
        zf.write(qss_path, "theme.qss")


def unpackTheme(
    altheme_path: str,
    output_dir: str
):
    """
        Extract a .altheme file to a directory.

        Performs Zip Slip validation before extraction.

        Args:
            altheme_path (str): Path to the .altheme file.
            output_dir (str): Directory to extract contents into.

        Raises:
            FileNotFoundError: If altheme_path does not exist.
            ValueError: If a zip entry contains an unsafe path.
    """

    if not os.path.isfile(altheme_path):
        raise FileNotFoundError(altheme_path)
    os.makedirs(output_dir, exist_ok=True)
    with zipfile.ZipFile(altheme_path, "r") as zf:
        for name in zf.namelist():
            if name.startswith("/") or ".." in name:
                raise ValueError(f"不安全的 .altheme 入口: {name}")
        zf.extractall(output_dir)


def readThemeInfo(
    altheme_path: str
) -> dict:
    """
        Read only the info.json metadata from a .altheme file.

        Args:
            altheme_path (str): Path to the .altheme file.

        Returns:
            dict: The theme metadata dictionary.

        Raises:
            FileNotFoundError: If altheme_path does not exist.
            ValueError: If the .altheme does not contain info.json.
    """

    if not os.path.isfile(altheme_path):
        raise FileNotFoundError(altheme_path)
    with zipfile.ZipFile(altheme_path, "r") as zf:
        if "info.json" not in zf.namelist():
            raise ValueError("无效的 .altheme: 缺少 info.json")
        with zf.open("info.json") as fh:
            info = json.loads(fh.read().decode("utf-8"))
        if "name" not in info:
            raise ValueError("无效的 .altheme: info.json 缺少 'name' 字段")
        return info


def wrapQssToAtheme(
    qss_path: str,
    output_path: str,
    current_theme: str
):
    """
        Wrap a bare .qss file into a .altheme file with auto-generated metadata.

        The generated info.json uses the filename as the theme name
        and sets default values for author and brief.

        Args:
            qss_path (str): Path to the bare .qss stylesheet file.
            output_path (str): Destination path for the .altheme file.
            current_theme (str): The need_theme value to embed in metadata
                                 ("light", "dark", or "both").

        Raises:
            FileNotFoundError: If qss_path does not exist.
    """

    filename = os.path.splitext(os.path.basename(qss_path))[0]
    info = {
        "name": filename,
        "author": "未知",
        "need_theme": current_theme,
        "brief": "没有相关简介"
    }
    packTheme(qss_path, info, output_path)
