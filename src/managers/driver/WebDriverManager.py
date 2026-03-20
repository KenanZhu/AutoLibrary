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
import packaging.version as ver

from enum import Enum
from pathlib import Path
from typing import Optional, Callable

from managers.driver.WebBrowserDetector import (
    WebBrowserType, WebBrowserArch, WebBrowserInfo, WebBrowserDetector
)
from managers.driver.WebDriverDownloader import (
    WebDriverArch, WebDriverType,
    ChromeDriverDownloader, FirefoxDriverDownloader, EdgeDriverDownloader
)


class DriverStatus(Enum):
    """
        Web driver status.
    """

    NOT_INSTALLED = 0
    INSTALLED = 1
    DOWNLOADING = 2
    ERROR = 3


class WebDriverInfo:
    """
        Web driver information.

        Attributes:
            browser_info (WebBrowserInfo): Web browser information
            driver_type (WebDriverType): Web driver type
            driver_version (str): Web driver version
            driver_path (Optional[Path]): Web driver executable file path
            driver_status (DriverStatus): Web driver status
    """

    def __init__(
        self,
        browser_info: WebBrowserInfo
    ):

        self.browser_info = browser_info
        self.driver_type = WebDriverType(browser_info.browser_type.value)
        self.driver_version = ""
        self.driver_path: Optional[Path] = None
        self.driver_status = DriverStatus.NOT_INSTALLED


class WebDriverManager:
    """
        Web Driver Manager Singleton Class

        Args:
            driver_dir (str): The directory to store web drivers.
    """

    def __init__(
        self,
        driver_dir: str
    ):

        self.__driver_dir = os.path.abspath(driver_dir)
        self.__browser_detector = WebBrowserDetector()
        self.__driver_infos: list[WebDriverInfo] = []
        self.__initialized = False
        self.__lock = threading.Lock()

        self.initialize()


    def initialize(
        self
    ):

        if self.__initialized:
            return
        os.makedirs(self.__driver_dir, exist_ok=True)
        self._detectBrowsers()
        self._checkDriverStatus()
        self.__initialized = True


    def _detectBrowsers(
        self
    ):

        with self.__lock:
            browser_infos = self.__browser_detector.detect()
            self.__driver_infos = [WebDriverInfo(info) for info in browser_infos]


    def _checkDriverStatus(
        self
    ):

        with self.__lock:
            for driver_info in self.__driver_infos:
                driver_arch = self._mapWebBrowserArch(
                    driver_info.browser_info.browser_type,
                    driver_info.browser_info.browser_arch
                )
                driver_path = self._getDriverPath(
                    driver_info.driver_type,
                    driver_arch
                )
                if driver_path and driver_path.exists() and driver_path.is_file():
                    driver_info.driver_path = driver_path
                    driver_info.driver_status = DriverStatus.INSTALLED
                    try:
                        driver_info.driver_version = self._getDriverVersion(
                            driver_info.driver_type,
                            driver_info.driver_info.browser_version
                        )
                    except Exception:
                        driver_info.driver_status = DriverStatus.ERROR


    def _mapWebBrowserArch(
        self,
        browser_type: WebBrowserType,
        browser_arch: WebBrowserArch
    ) -> WebDriverArch:

        if browser_type == WebBrowserType.CHROME:
            if browser_arch == WebBrowserArch.WINX86_32:
                return WebDriverArch.Chrome.WINX86_32
            elif browser_arch == WebBrowserArch.WINX86_64:
                return WebDriverArch.Chrome.WINX86_64
            elif browser_arch == WebBrowserArch.WINARM:
                raise ValueError("Chrome 不支持 Windows ARM 架构")
            elif browser_arch == WebBrowserArch.LINUXX86_32:
                raise ValueError("Chrome 不支持 Linux x86_32 架构")
            elif browser_arch == WebBrowserArch.LINUXX86_64:
                return WebDriverArch.Chrome.LINUXX86_64
            elif browser_arch == WebBrowserArch.LINUXARM:
                raise ValueError("Chrome 不支持 Linux ARM 架构")
            elif browser_arch == WebBrowserArch.MACX86_64:
                return WebDriverArch.Chrome.MACX86_64
            elif browser_arch == WebBrowserArch.MACARM:
                return WebDriverArch.Chrome.MACARM
            else:
                raise ValueError(f"不支持的 Chrome 浏览器架构 : {browser_arch}")
        elif browser_type == WebBrowserType.FIREFOX:
            if browser_arch == WebBrowserArch.WINX86_32:
                return WebDriverArch.Firefox.WINX86_32
            elif browser_arch == WebBrowserArch.WINX86_64:
                return WebDriverArch.Firefox.WINX86_64
            elif browser_arch == WebBrowserArch.WINARM:
                return WebDriverArch.Firefox.WINARM
            elif browser_arch == WebBrowserArch.LINUXX86_32:
                return WebDriverArch.Firefox.LINUXX86_32
            elif browser_arch == WebBrowserArch.LINUXX86_64:
                return WebDriverArch.Firefox.LINUXX86_64
            elif browser_arch == WebBrowserArch.LINUXARM:
                return WebDriverArch.Firefox.LINUXARM
            elif browser_arch == WebBrowserArch.MACX86_64:
                return WebDriverArch.Firefox.MACX86_64
            elif browser_arch == WebBrowserArch.MACARM:
                return WebDriverArch.Firefox.MACARM
            else:
                raise ValueError(f"不支持的 Firefox 浏览器架构 : {browser_arch}")
        elif browser_type == WebBrowserType.EDGE:
            if browser_arch == WebBrowserArch.WINX86_32:
                return WebDriverArch.Edge.WINX86_32
            elif browser_arch == WebBrowserArch.WINX86_64:
                return WebDriverArch.Edge.WINX86_64
            elif browser_arch == WebBrowserArch.WINARM:
                return WebDriverArch.Edge.WINARM
            elif browser_arch == WebBrowserArch.LINUXX86_32:
                raise ValueError("Edge 不支持 Linux x86_32 架构")
            elif browser_arch == WebBrowserArch.LINUXX86_64:
                return WebDriverArch.Edge.LINUXX86_64
            elif browser_arch == WebBrowserArch.LINUXARM:
                raise ValueError("Edge 不支持 Linux ARM 架构")
            elif browser_arch == WebBrowserArch.MACX86_64:
                return WebDriverArch.Edge.MACX86_64
            elif browser_arch == WebBrowserArch.MACARM:
                return WebDriverArch.Edge.MACARM
            else:
                raise ValueError(f"不支持的 Edge 浏览器架构 : {browser_arch}")
        else:
            raise ValueError(f"不支持的 Web 浏览器类型 : {browser_type}")


    def _mapFirefoxDriverVersion(
        self,
        version: str
    ) -> str:

        version_mapping = [
            (ver.Version("128.0"), ver.Version("999.0"), "0.36.0"),
            (ver.Version("115.0"), ver.Version("127.0"), "0.35.0"),
            (ver.Version("91.0"),  ver.Version("114.0"), "0.34.0"),
            (ver.Version("91.0"),  ver.Version("120.0"), "0.33.0"),
            (ver.Version("91.0"),  ver.Version("120.0"), "0.32.0"),
            (ver.Version("91.0"),  ver.Version("120.0"), "0.31.0"),
            (ver.Version("78.0"),  ver.Version("90.0"),  "0.30.0"),
            (ver.Version("60.0"),  ver.Version("90.0"),  "0.29.0"),
            (ver.Version("60.0"),  ver.Version("90.0"),  "0.28.0"),
            (ver.Version("60.0"),  ver.Version("90.0"),  "0.27.0"),
            (ver.Version("57.0"),  ver.Version("90.0"),  "0.26.0"),
            (ver.Version("55.0"),  ver.Version("62.0"),  "0.25.0"),
            (ver.Version("55.0"),  ver.Version("62.0"),  "0.24.0"),
            (ver.Version("57.0"),  ver.Version("79.0"),  "0.23.0"),
            (ver.Version("57.0"),  ver.Version("79.0"),  "0.22.0"),
            (ver.Version("57.0"),  ver.Version("79.0"),  "0.21.0"),
            (ver.Version("55.0"),  ver.Version("62.0"),  "0.20.0"),
            (ver.Version("55.0"),  ver.Version("62.0"),  "0.19.0"),
            (ver.Version("53.0"),  ver.Version("62.0"),  "0.18.0"),
            (ver.Version("52.0"),  ver.Version("62.0"),  "0.17.0"),
        ]

        try:
            firefox_version = ver.Version(version)
            for min_ver, max_ver, gecko_ver in version_mapping:
                if min_ver <= firefox_version <= max_ver:
                    return gecko_ver
            raise ValueError(
                f"不支持的 Firefox 版本 : {version}"
                f"Firefox 版本 52 及以上受支持"
            )
        except Exception as e:
            raise ValueError(f"无效的 Firefox 版本格式 : {version}") from e


    def _getDriverPath(
        self,
        driver_type: WebDriverType,
        driver_arch: WebDriverArch
    ) -> Optional[Path]:

        if driver_type == WebDriverType.CHROME:
            driver_name = "chromedriver"
        elif driver_type == WebDriverType.FIREFOX:
            driver_name = "geckodriver"
        elif driver_type == WebDriverType.EDGE:
            driver_name = "msedgedriver"
        else:
            return None
        is_win = driver_arch in [
            WebDriverArch.Chrome.WINX86_32,
            WebDriverArch.Chrome.WINX86_64,
            WebDriverArch.Firefox.WINX86_32,
            WebDriverArch.Firefox.WINX86_64,
            WebDriverArch.Edge.WINX86_32,
            WebDriverArch.Edge.WINX86_64,
        ]
        exe_name = f"{driver_name}.exe" if is_win else driver_name
        driver_dir = Path(self.__driver_dir) / driver_type.value / driver_arch.value
        driver_path = driver_dir / exe_name
        if driver_path.exists() and driver_path.is_file():
            return driver_path
        return None


    def _getDriverVersion(
        self,
        driver_type: WebDriverType,
        browser_version: str
    ) -> str:

        if driver_type == WebDriverType.FIREFOX:
            return self._mapFirefoxDriverVersion(browser_version)
        return browser_version


    def refresh(
        self
    ):

        with self.__lock:
            self._detectBrowsers()
            self._checkDriverStatus()


    def getDriverInfos(
        self
    ) -> list[WebDriverInfo]:

        with self.__lock:
            return self.__driver_infos.copy()


    def getDriverInfo(
        self,
        driver_type: WebDriverType
    ) -> Optional[WebDriverInfo]:

        with self.__lock:
            for driver_info in self.__driver_infos:
                if driver_info.driver_type == driver_type:
                    return driver_info
            return None


    def getDriverPath(
        self,
        driver_type: WebDriverType
    ) -> Optional[Path]:

        driver_info = self.getDriverInfo(driver_type)
        if driver_info and driver_info.driver_status == DriverStatus.INSTALLED:
            return driver_info.driver_path
        return None


    def installDriver(
        self,
        driver_type: WebDriverType,
        progress_callback: Optional[Callable[[int, int, float, str], None]] = None
    ) -> Optional[Path]:

        with self.__lock:
            driver_info = self.getDriverInfo(driver_type)
            if not driver_info:
                raise ValueError(f"未找到类型为 {driver_type} 的浏览器")
            if driver_info.driver_status == DriverStatus.DOWNLOADING:
                raise ValueError(f"{driver_type} 驱动正在下载中")
            driver_info.driver_status = DriverStatus.DOWNLOADING
        try:
            driver_arch = self._mapWebBrowserArch(
                driver_info.browser_info.browser_type,
                driver_info.browser_info.browser_arch
            )
            browser_version = driver_info.browser_info.browser_version
            driver_version = self._getDriverVersion(driver_type, browser_version)
            downloader = None
            if driver_type == WebDriverType.CHROME:
                downloader = ChromeDriverDownloader(
                    version=driver_version,
                    arch=driver_arch,
                    download_dir=self.__driver_dir
                )
            elif driver_type == WebDriverType.FIREFOX:
                downloader = FirefoxDriverDownloader(
                    version=driver_version,
                    arch=driver_arch,
                    download_dir=self.__driver_dir
                )
            elif driver_type == WebDriverType.EDGE:
                downloader = EdgeDriverDownloader(
                    version=driver_version,
                    arch=driver_arch,
                    download_dir=self.__driver_dir
                )
            if downloader is None:
                raise ValueError(f"不支持的 Web Driver 类型 : {driver_type}")

            driver_path = downloader.download(progress_callback=progress_callback)
            with self.__lock:
                if driver_path:
                    driver_info.driver_path = driver_path
                    driver_info.driver_version = driver_version
                    driver_info.driver_status = DriverStatus.INSTALLED
                else:
                    driver_info.driver_status = DriverStatus.ERROR
            return driver_path
        except Exception as e:
            with self.__lock:
                driver_info.driver_status = DriverStatus.ERROR
            raise


    def driverDir(
        self
    ) -> str:

        return self.__driver_dir


# WebDriverManager singleton instance.
_webdriver_manager_instance = None

# Singleton instance lock.
_instance_lock = threading.Lock()

def instance(
    driver_dir: str = ""
) -> WebDriverManager:

    global _webdriver_manager_instance
    with _instance_lock:
        if _webdriver_manager_instance is None:
            if not driver_dir:
                raise ValueError("WebDriverManager 需要驱动目录参数")
            _webdriver_manager_instance = WebDriverManager(driver_dir)
        else:
            if driver_dir and _webdriver_manager_instance.driverDir() != os.path.abspath(driver_dir):
                raise ValueError("WebDriverManager 的实例已初始化,不能使用不同的驱动目录")
    return _webdriver_manager_instance
