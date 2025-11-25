# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import json


class ConfigWriter:

    def __init__(
        self,
        config_path: str,
        config_data: dict
    ):

        self.__config_path = config_path
        self.__config_data = config_data if config_data is not None else {}
        if config_data is None:
            return None
        if not self.__writeConfig():
            return None


    def __writeConfig(
        self
    ) -> bool:

        try:
            with open(self.__config_path, "w") as f:
                json.dump(self.__config_data, f, indent=4, sort_keys=False)
            return True
        except:
            return False


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
        value: dict
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