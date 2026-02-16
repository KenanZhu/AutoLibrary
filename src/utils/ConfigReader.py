# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import json
import copy

from typing import Any


class ConfigReader:
    """
        Config reader class.

        This class is used to read config file in JSON format.

        Args:
            config_path (str): The path of config file.

        Examples:
            >>>  print(open("config.json", "r", encoding="utf-8").read())
            {
                "key1": {
                    "key2": "value1"
                }
            }
            >>> config_reader = ConfigReader("config.json")
            >>> config_reader.get("key1/key2")
            "value1"
    """

    def __init__(
        self,
        config_path: str
    ):

        self.__config_path = config_path
        self.__config_data = None
        self.__readConfig()


    def __readConfig(
        self
    ):

        try:
            with open(self.__config_path, 'r', encoding='utf-8') as file:
                self.__config_data = json.load(file)
        except FileNotFoundError as e:
            raise Exception(f"配置文件不存在: {self.__config_path}") from e
        except PermissionError as e:
            raise Exception(f"没有足够的权限读取配置文件: {self.__config_path}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 解析错误: {self.__config_path}") from e
        except Exception as e:
            raise Exception(f"读取配置文件时未知错误: {e}") from e


    def getConfigs(
        self
    ) -> dict:

        return self.__config_data.copy()


    def getConfig(
        self,
        key: str
    ) -> Any:

        config = self.__config_data.get(key, {})
        return copy.deepcopy(config)


    def get(
        self,
        key: str,
        default: Any = None
    ) -> Any:

        keys = key.split('/')
        current = self.__config_data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return copy.deepcopy(current)


    def hasConfig(
        self,
        key: str
    ) -> bool:

        return self.getConfig(key) != {}


    def reReadConfig(
        self
    ) -> bool:

        return self.__readConfig()


    def configPath(
        self
    ) -> str:

        return self.__config_path
