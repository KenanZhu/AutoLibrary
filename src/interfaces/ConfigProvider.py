# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Protocol


class ConfigType(Enum):
    """
        Config type enum. Values represent the default filename.
    """

    GLOBAL = "autolibrary.json"
    BULLETIN = "bulletin.json"
    TIMERTASK = "timer_task.json"


@dataclass(frozen=True)
class ConfigPath:
    """
        A typed configuration path that carries both the config file
        and the dot-separated key in a single object.

        Consumers pass this directly to ConfigProvider.get/set,
        eliminating the need to import ConfigType separately.
    """

    config_type: ConfigType
    key: str = ""


class CfgKey:
    """
        Type-safe hierarchical configuration key constants.

        Each leaf is a ConfigPath that can be passed directly to
        ``ConfigProvider.get()`` or ``ConfigProvider.set()``.

        Usage::

            CfgKey.GLOBAL.AUTOMATION.RUN_PATH.PATHS
            # -> ConfigPath(ConfigType.GLOBAL, "automation.run_path.paths")

            config.get(CfgKey.GLOBAL.AUTOMATION.RUN_PATH.PATHS, [])
            config.set(CfgKey.GLOBAL.AUTOMATION.RUN_PATH.PATHS, value)
    """

    class GLOBAL:
        class AUTOMATION:
            ROOT = ConfigPath(ConfigType.GLOBAL, "automation")

            class RUN_PATH:
                ROOT = ConfigPath(ConfigType.GLOBAL, "automation.run_path")
                CURRENT = ConfigPath(ConfigType.GLOBAL, "automation.run_path.current")
                PATHS = ConfigPath(ConfigType.GLOBAL, "automation.run_path.paths")

            class USER_PATH:
                ROOT = ConfigPath(ConfigType.GLOBAL, "automation.user_path")
                CURRENT = ConfigPath(ConfigType.GLOBAL, "automation.user_path.current")
                PATHS = ConfigPath(ConfigType.GLOBAL, "automation.user_path.paths")

        class APPEARANCE:
            ROOT = ConfigPath(ConfigType.GLOBAL, "appearance")
            THEME = ConfigPath(ConfigType.GLOBAL, "appearance.theme")
            STYLE = ConfigPath(ConfigType.GLOBAL, "appearance.style")
            CUSTOM_QSS = ConfigPath(ConfigType.GLOBAL, "appearance.custom_qss")

    class TIMERTASK:
        ROOT = ConfigPath(ConfigType.TIMERTASK, "")
        TIMER_TASKS = ConfigPath(ConfigType.TIMERTASK, "timer_tasks")

    class BULLETIN:
        ROOT = ConfigPath(ConfigType.BULLETIN, "")
        BULLETIN = ConfigPath(ConfigType.BULLETIN, "bulletin")
        LAST_SYNC_TIME = ConfigPath(ConfigType.BULLETIN, "last_sync_time")


class ConfigProvider(Protocol):
    """
        Abstract interface for configuration storage access.

        Concrete implementations (e.g. ConfigManager) conform to
        this protocol structurally rather than through explicit
        inheritance.
    """

    def get(
        self,
        key: ConfigPath,
        default: Optional[Any] = None
    ) -> Any:
        """
            Retrieve a configuration value.

            Args:
                key: A ConfigPath object specifying which config file
                     and key to read from.
                default: Fallback value if the key is not found.

            Returns:
                The configuration value at the given key path.
        """
        ...

    def set(
        self,
        key: ConfigPath,
        value: Any = None
    ) -> None:
        """
            Set a configuration value and persist to disk.

            Args:
                key: A ConfigPath object specifying which config file
                     and key to write to.
                value: The value to store.
        """
        ...
