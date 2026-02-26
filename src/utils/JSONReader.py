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


class JSONReader:
    """
        JSON reader class.

        This class is used to read JSON file.

        Args:
            json_path (str): The path of JSON file.

        Examples:
            >>>  print(open("config.json", "r", encoding="utf-8").read())
            {
                "key1": {
                    "key2": "value1"
                }
            }
            >>> json_reader = JSONReader("config.json")
            >>> data = json_reader.data()
            >>> data["key1"]["key2"]
            "value1"
    """

    def __init__(
        self,
        json_path: str
    ):

        self.__json_path = os.path.abspath(json_path)
        self.__json_data = None
        self.__read()


    def __read(
        self
    ):

        try:
            with open(self.__json_path, 'r', encoding='utf-8') as file:
                self.__json_data = json.load(file)
        except FileNotFoundError as e:
            raise Exception(f"文件不存在: {self.__json_path}") from e
        except PermissionError as e:
            raise Exception(f"没有足够的权限读取文件: {self.__json_path}") from e
        except json.JSONDecodeError as e:
            raise Exception(f"JSON 解析错误: {self.__json_path}") from e
        except Exception as e:
            raise Exception(f"读取文件时发生未知错误: {e}") from e


    def read(
        self
    ) -> bool:

        try:
            self.__read()
        except:
            return False
        return True


    def data(
        self
    ) -> dict:

        return self.__json_data.copy()


    def path(
        self
    ) -> str:

        return self.__json_path
