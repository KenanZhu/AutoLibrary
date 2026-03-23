# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 - 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import managers.config.ConfigManager as ConfigManager

class ConfigUtils:
    """
        Config utilities class.
    """

    @staticmethod
    def getAutomationConfigPaths(
    ) -> dict[str]:
        """
            Get validated automation config paths from ConfigManager instance.
            These function will validate the config paths and return the validated paths in a dict.

            Returns:
                dict[str]: Validated automation config paths (include user and run config paths).
        """
        cfg_mgr = ConfigManager.instance() # config manager instance

        config_paths = {"run": "", "user": ""}
        auto_config = cfg_mgr.get(ConfigManager.ConfigType.GLOBAL, "automation", {})
        for cfg_type in ["run", "user"]:
                paths = auto_config.get(f"{cfg_type}_path", {}).get("paths", [])
                index = auto_config.get(f"{cfg_type}_path", {}).get("current", 0)
                if paths == []:
                    paths.append(os.path.join(cfg_mgr.configDir(), f"{cfg_type}.json"))
                if index < 0:
                    index = 0
                if index >= len(paths):
                    index = len(paths) - 1
                config_paths[cfg_type] = paths[index]
                data = {"current": index, "paths": paths}
                auto_config[f"{cfg_type}_path"] = data
        cfg_mgr.set(ConfigManager.ConfigType.GLOBAL, "automation", auto_config)
        return config_paths