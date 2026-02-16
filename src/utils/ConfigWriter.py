# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import json

from typing import Any


class ConfigWriter:
    """
        Config writer class.

        This class is used to write config file in JSON format.

        Args:
            config_path (str): The path of config file.
            config_data (dict): The config data to be written.

        Examples:
            >>> config_data = {
            ...     "key1": {
            ...         "key2": "value1"
            ...     }
            ... }
            >>> config_writer = ConfigWriter("config.json", config_data)
            >>> config_writer.set("key1/key2", "value1")
            True
            >>>  print(open("config.json", "r", encoding="utf-8").read())
            {
                "key1": {
                    "key2": "value1"
                }
            }
    """

    def __init__(
        self,
        config_path: str,
        config_data: dict
    ):

        self.__config_path = config_path
        self.__config_data = config_data.copy() if config_data is not None else {}
        self.__writeConfig()


    def __writeConfig(
        self
    ):

        try:
            with open(self.__config_path, "w", encoding="utf-8") as f:
                json.dump(self.__config_data, f, indent=4, sort_keys=False)
        except PermissionError as e:
            raise Exception(f"没有足够的权限写入配置文件: {self.__config_path}") from e
        except IOError as e:
            raise Exception(f"写入配置文件时发生 IO 错误: {self.__config_path}") from e
        except TypeError as e:
            raise Exception(f"配置数据包含无法 JSON 序列化的类型: {e}") from e
        except Exception as e:
            raise Exception(f"写入配置文件时未知错误: {e}") from e


    def setConfigs(
        self,
        configs: dict
    ) -> bool:

        self.__config_data = configs
        return self.__writeConfig()


    def setConfig(
        self,
        key: str,
        value: dict
    ) -> bool:

        self.__config_data[key] = value
        return self.__writeConfig()


    def set(
        self,
        key: str,
        value: Any
    ) -> bool:

        keys = key.replace("\\", "/").split("/")
        current = self.__config_data
        for k in keys[:-1]:
            if k not in current or not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
        return self.__writeConfig()


    def reWriteConfig(
        self
    ) -> bool:

        return self.__writeConfig()


    def configPath(
        self
    ) -> str:

        return self.__config_path