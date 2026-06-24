# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import threading

from datetime import datetime, timedelta
from typing import Optional

from interfaces.ConfigProvider import (
    CfgKey,
    ConfigProvider
)
from managers.config.ConfigManager import instance as configInstance


class BulletinManager:
    """
        Bulletin Manager Singleton Class

        Manages bulletin data persistence via ConfigManager and provides
        merge, read-status and sync-parameter logic. The HTTP fetch and
        UI concerns are handled by the GUI layer.
    """

    def __init__(
        self
    ):

        self.__lock = threading.Lock()
        self.__cfg: ConfigProvider = configInstance()

    def bulletins(
        self
    ) -> list[dict]:
        """
            Get cached bulletins.

            Returns:
                list[dict]: Cached bulletin list.
        """

        return self.__cfg.get(CfgKey.BULLETIN.BULLETIN, [])

    def setBulletins(
        self,
        bulletins: list[dict]
    ):
        """
            Replace the bulletin cache.

            Args:
                bulletins (list[dict]): Bulletin list to store.
        """

        self.__cfg.set(CfgKey.BULLETIN.BULLETIN, bulletins)

    def lastSyncTime(
        self
    ) -> Optional[str]:
        """
            Get last sync time string.

            Returns:
                Optional[str]: ISO-format last sync time, or None.
        """

        return self.__cfg.get(CfgKey.BULLETIN.LAST_SYNC_TIME, None)

    def setLastSyncTime(
        self,
        value: Optional[str]
    ):
        """
            Set last sync time.

            Args:
                value (Optional[str]): ISO-format datetime string.
        """

        self.__cfg.set(CfgKey.BULLETIN.LAST_SYNC_TIME, value)

    def autoFetch(
        self
    ) -> bool:
        """
            Get auto-fetch-on-startup setting.

            Returns:
                bool: Whether to fetch bulletins on application startup.
        """

        return self.__cfg.get(CfgKey.GLOBAL.BULLETIN.AUTO_FETCH, False)

    def serverUrl(
        self
    ) -> str:
        """
            Get bulletin server URL.

            Returns:
                str: Server base URL.
        """

        return self.__cfg.get(
            CfgKey.GLOBAL.BULLETIN.SERVER_URL,
            "https://api.autolibrary.kenanzhu.com"
        )

    def syncInterval(
        self
    ) -> int:
        """
            Get auto-sync interval in minutes.

            Values below 1 are clamped to 5 minutes.

            Returns:
                int: Sync interval (minutes), minimum 1.
        """

        interval = self.__cfg.get(CfgKey.GLOBAL.BULLETIN.SYNC_INTERVAL, 10)
        if interval < 1:
            return 5
        return interval

    def apiUrl(
        self
    ) -> str:
        """
            Build the full bulletin API endpoint URL.

            Returns:
                str: Full API URL (base + /bulletins).
        """

        base = self.serverUrl().rstrip("/")
        return f"{base}/bulletins"

    def isFirstSync(
        self
    ) -> bool:
        """
            Check whether this is the first sync.

            Returns:
                bool: True if no cached bulletins or no last sync time.
        """

        last = self.lastSyncTime()
        bulletins = self.bulletins()
        return last is None or not bulletins

    def shouldFullSync(
        self
    ) -> bool:
        """
            Check whether a full sync is needed.

            A full sync is triggered when the last sync time is more than
            one hour ago.

            Returns:
                bool: True if a full sync should be performed.
        """

        last = self.lastSyncTime()
        if last is None:
            return True
        try:
            last_dt = datetime.fromisoformat(last)
            return (datetime.now().astimezone() - last_dt) > timedelta(hours=1)
        except (ValueError, TypeError):
            return True

    def getSyncDateTimeAndRange(
        self
    ) -> dict:
        """
            Calculate the date / time / range_hour query parameters.

            Returns:
                dict: Keys "date", "time", "range_hour" for the API request.
        """

        if self.isFirstSync():
            start_date = datetime.now() - timedelta(days=7)
            range_hour = str(24 * (7 + 1))
        elif self.shouldFullSync():
            bulletins = self.bulletins()
            earliest = min(bulletins, key=lambda x: x.get("dateTime", ""))
            start_date = datetime.fromisoformat(earliest["dateTime"])
            diff = datetime.now().astimezone() - start_date
            range_hour = str(int(diff.total_seconds() / 3600) + 1)
        else:
            bulletins = self.bulletins()
            latest = max(bulletins, key=lambda x: x.get("dateTime", ""))
            start_date = datetime.fromisoformat(latest["dateTime"])
            diff = datetime.now().astimezone() - start_date
            range_hour = str(int(diff.total_seconds() / 3600) + 1)
        return {
            "date": start_date.strftime("%Y-%m-%d"),
            "time": start_date.strftime("%H:%M:%S"),
            "range_hour": range_hour,
        }

    def updateAndMergeBulletins(
        self,
        new_bulletins: list[dict],
        delete_ids: list[str]
    ) -> list[dict]:
        """
            Merge incoming bulletins into the cache.

            New bulletins are added with isNew=True. Existing bulletins
            keep their current isNew state. Entries listed in delete_ids
            are removed.

            Args:
                new_bulletins (list[dict]): Incoming bulletin list.
                delete_ids (list[str]): IDs to remove.

            Returns:
                list[dict]: Merged bulletin list sorted by id.
        """

        with self.__lock:
            delete_set = set(delete_ids)
            bulletins_dict = {b["id"]: b for b in self.bulletins()}
            for bulletin in new_bulletins:
                bid = bulletin["id"]
                if bid in delete_set:
                    bulletins_dict.pop(bid, None)
                    continue
                if bid not in bulletins_dict:
                    bulletin["isNew"] = True
                else:
                    bulletin["isNew"] = bulletins_dict[bid].get("isNew", True)
                bulletins_dict[bid] = bulletin
            for bid in delete_set:
                bulletins_dict.pop(bid, None)
            result = list(bulletins_dict.values())
            result.sort(key=lambda x: int(x["id"]))
            self.setBulletins(result)
            return result

    def markBulletinAsRead(
        self,
        bulletin_id: str
    ):
        """
            Mark a bulletin as read by its id.

            Args:
                bulletin_id (str): The bulletin id.
        """

        with self.__lock:
            bulletins = self.bulletins()
            for b in bulletins:
                if b["id"] == bulletin_id:
                    b["isNew"] = False
                    self.setBulletins(bulletins)
                    break


# BulletinManager singleton instance.
_bulletin_manager_instance = None

# Singleton instance lock.
_instance_lock = threading.Lock()


def instance(
) -> BulletinManager:
    """
        Get the BulletinManager singleton instance.

        Returns:
            BulletinManager: The singleton BulletinManager instance.
    """

    global _bulletin_manager_instance
    with _instance_lock:
        if _bulletin_manager_instance is None:
            _bulletin_manager_instance = BulletinManager()
    return _bulletin_manager_instance
