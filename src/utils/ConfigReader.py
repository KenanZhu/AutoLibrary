# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import json


class ConfigReader:

    def __init__(
        self,
        config_path: str
    ):

        self._config_path = config_path
        self._config_data = {}
        if not self.__readConfig():
            return None


    def __readConfig(
        self
    ) -> bool:

        try:
            with open(self._config_path, 'r', encoding='utf-8') as file:
                self._config_data = json.load(file)
            return True
        except Exception as e:
            print(f"Error reading config file: {e}")
            return False


    def getConfigs(
        self
    ) -> dict:

        return self._config_data.copy()


    def getConfig(
        self,
        key: str
    ) -> dict:

        return self._config_data.get(key, {})


    def get(
        self,
        key: str,
        default: any = None
    ) -> any:

        keys = key.split('/')
        current = self._config_data
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        return current


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

        return self._config_path
