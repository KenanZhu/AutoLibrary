# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import json


class JSONWriter:
    """
        JSON writer class.

        This class is used to write JSON file.

        Args:
            json_path (str): The path of JSON file.
            json_data (dict): The JSON data to be written.

        Examples:
            >>> json_data = {
            ...     "key1": {
            ...         "key2": "value1"
            ...     }
            ... }
            >>> json_writer = JSONWriter("config.json", json_data)
            >>> print(open("config.json", "r", encoding="utf-8").read())
            {
                "key1": {
                    "key2": "value1"
                }
            }
    """

    def __init__(
        self,
        json_path: str,
        json_data: dict
    ):

        self.__json_path = os.path.abspath(json_path)
        self.__json_data = json_data.copy() if json_data is not None else {}
        self.__write()


    def __write(
        self
    ):

        try:
            with open(self.__json_path, "w", encoding="utf-8") as f:
                json.dump(self.__json_data, f, indent=4, sort_keys=False)
        except PermissionError as e:
            raise Exception(f"没有足够的权限写入文件: {self.__json_path}") from e
        except IOError as e:
            raise Exception(f"写入文件时发生 IO 错误: {self.__json_path}") from e
        except TypeError as e:
            raise Exception(f"JSON 数据包含无法 JSON 序列化的类型: {e}") from e
        except Exception as e:
            raise Exception(f"写入文件时发生未知错误: {e}") from e


    def write(
        self
    ) -> bool:

        try:
            self.__write()
        except:
            return False
        return True


    def path(
        self
    ) -> str:

        return self.__json_path