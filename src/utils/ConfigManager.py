# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import threading

from enum import Enum
from typing import Any, Optional

from utils.JSONReader import JSONReader
from utils.JSONWriter import JSONWriter


# This config manager class only responsible for global and other
# unconfigurable config files.


class ConfigType(Enum):
    """
        Config type class. Values represent the default filename.
    """
    GLOBAL = "autolibrary.json" # Global config file.
    BULLETIN = "bulletin.json" # Bulletin board config file.
    TIMERTASK = "timer_task.json" # Timer task config file.


class ConfigTemplate:
    """
        Config template class.
    """

    def __init__(
        self,
        config_type: ConfigType
    ):

        self.__config_type = config_type


    def template(
        self
    ) -> dict:
        """
            Get config template.

            Returns:
                dict: Config template.
        """
        match self.__config_type:
            case ConfigType.GLOBAL:
                return {
                    "automation": {
                        "run_path": {
                            "current": 0,
                            "paths": []
                        },
                        "user_path": {
                            "current": 0,
                            "paths": []
                        }
                    }
                }
            case ConfigType.BULLETIN:
                return {
                    "bulletin": [],
                    "last_sync_time": None
                }
            case ConfigType.TIMERTASK:
                return {
                    "timer_tasks": []
                }
            case _:
                return {}


class ConfigManager:

    def __init__(
        self,
        config_dir: str
    ):

        self.__config_dir = os.path.abspath(config_dir)
        self.__config_lock = threading.Lock()
        self.__config_data = {}

        self.initialize()


    def initialize(
        self
    ):

        for config_type in ConfigType:
            self.load(config_type)


    def load(
        self,
        config_type: ConfigType
    ):

        config_path = os.path.join(self.__config_dir, config_type.value)
        if os.path.exists(config_path):
            try:
                config_data = JSONReader(config_path).data()
                self.__config_data[config_type.value] = config_data
                return
            except:
                pass
        self.__config_data[config_type.value] = ConfigTemplate(config_type).template()
        JSONWriter(config_path, self.__config_data[config_type.value])


    def get(
        self,
        config_type: ConfigType,
        key: str = "",
        default: Optional[Any] = None
    ) -> Any:

        with self.__config_lock:
            config_data = self.__config_data[config_type.value]
            if key == "":
                return config_data
            keys = key.split('.')
            for k in keys[:-1]:
                config_data = config_data.get(k, None)
                if config_data is None:
                    return default
            return config_data.get(keys[-1], default)


    def set(
        self,
        config_type: ConfigType,
        key: str = "",
        value: Any = None
    ):

        with self.__config_lock:
            root_data = self.__config_data[config_type.value]
            if key == "":
                self.__config_data[config_type.value] = value
            else:
                keys = key.split('.')
                config_data = root_data
                for k in keys[:-1]:
                    if k not in config_data:
                        config_data[k] = {}
                    config_data = config_data[k]
                config_data[keys[-1]] = value
        self.save(config_type)


    def save(
        self,
        config_type: ConfigType
    ):

        config_path = os.path.join(self.__config_dir, config_type.value)
        JSONWriter(config_path, self.__config_data[config_type.value])


    def appDir(
        self
    ) -> str:

        return self.__config_dir


_config_manager_instance = None

# Utility function to get config data (thread-safe and validated) from ConfigManager instance.
def getValidateAutomationConfigPaths(
) -> dict:
    """
        Get validated automation config paths from ConfigManager instance.
        These function will validate the config paths and return the validated paths in a dict.

        Returns:
            dict: Validated automation config paths.
    """
    config_paths = {"run": "", "user": ""}
    auto_config = _config_manager_instance.get(ConfigType.GLOBAL, "automation", {})
    for cfg_type in ["run", "user"]:
            paths = auto_config.get(f"{cfg_type}_path", {}).get("paths", [])
            index = auto_config.get(f"{cfg_type}_path", {}).get("current", 0)
            if paths == []:
                paths.append(os.path.join(_config_manager_instance.appDir(), f"{cfg_type}.json"))
            if index < 0:
                index = 0
            if index >= len(paths):
                index = len(paths) - 1
            config_paths[cfg_type] = paths[index]
            data = {"current": index, "paths": paths}
            auto_config[f"{cfg_type}_path"] = data
    _config_manager_instance.set(ConfigType.GLOBAL, "automation", auto_config)
    return config_paths

def getBaseConfigDir(
) -> str:

    return _config_manager_instance.appDir()

# Singleton instance of ConfigManager.
_instance_lock = threading.Lock()
def instance(
    config_dir: str = ""
) -> ConfigManager:
    """
        Initialize ConfigManager singleton instance.

        Args:
            config_dir (str): Config directory.
    """
    global _config_manager_instance
    with _instance_lock:
        if _config_manager_instance is None:
            _config_manager_instance = ConfigManager(config_dir)
        else:
            if config_dir == "":
                return _config_manager_instance
            if _config_manager_instance.appDir() != config_dir:
                raise ValueError(
                    "ConfigManager 的实例已初始化，不能使用不同的配置目录。")
    return _config_manager_instance
