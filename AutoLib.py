# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import queue

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service

from MsgBase import MsgBase
from LibLogin import LibLogin
from LibLogout import LibLogout
from LibReserve import LibReserve

from ConfigReader import ConfigReader


class AutoLib(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
    ):
        super().__init__(input_queue, output_queue)

        self.__system_config_reader = None
        self.__users_config_reader = None
        self.__driver = None


    def __initBrowserDriver(
        self
    ) -> bool:

        self._showTrace("正在初始化浏览器驱动......")
        edge_options = webdriver.EdgeOptions()

        if self.__system_config_reader.get("web_driver/headless"):
            edge_options.add_argument("--headless")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")

        edge_options.add_argument("--window-size=1280,720")
        edge_options.add_argument("--remote-allow-origins=*")

        # omit ssl errors and verbose log level
        edge_options.add_argument("--ignore-certificate-errors")
        edge_options.add_argument("--ignore-ssl-errors")
        edge_options.add_argument("--log-level=OFF")
        edge_options.add_argument("--silent")

        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option("useAutomationExtension", False)
        edge_options.add_argument("--disable-blink-features=AutomationControlled")
        edge_options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "\
            "AppleWebKit/537.36 (KHTML, like Gecko) "\
            "Chrome/120.0.0.0 "\
            "Safari/537.36 "\
            "Edg/120.0.0.0"
        )

        # init browser driver
        self.__driver_path = self.__system_config_reader.get("web_driver/driver_path")
        self.__driver_type = self.__system_config_reader.get("web_driver/driver_type")
        self.__driver_path = os.path.abspath(self.__driver_path)
        try:
            service = None
            if self.__driver_path:
                service = Service(executable_path=self.__driver_path)
            match self.__driver_type.lower():
                case "edge":
                    self.__driver = webdriver.Edge(service=service, options=edge_options)
                case "chrome":
                    self.__driver = webdriver.Chrome(service=service, options=edge_options)
                case "firefox":
                    self.__driver = webdriver.Firefox(service=service, options=edge_options)
                case _:
                    raise Exception(f"不支持的浏览器驱动类型: {self.__driver_type}")
            self.__driver.implicitly_wait(10)
            self.__driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except Exception as e:
            self._showTrace(f"浏览器驱动初始化失败: {e}")
            return False
        # init library operators
        self.__lib_login = LibLogin(self._input_queue, self._output_queue, self.__driver)
        self.__lib_logout = LibLogout(self._input_queue, self._output_queue, self.__driver)
        self.__lib_reserve = LibReserve(self._input_queue, self._output_queue, self.__driver)
        self._showTrace(f"浏览器驱动已初始化, 类型: {self.__driver_type}, 路径: {self.__driver_path}")
        return True


    def __waitResponseLoad(
        self,
    ) -> bool:

        # wait for page load
        try:
            WebDriverWait(self.__driver, 5).until( # title contains "首页"
                EC.title_contains("首页")
            )
            WebDriverWait(self.__driver, 2).until( # username field presence
                EC.presence_of_element_located((By.NAME, "username"))
            )
            WebDriverWait(self.__driver, 2).until( # password field presence
                EC.presence_of_element_located((By.NAME, "password"))
            )
            WebDriverWait(self.__driver, 2).until( # captcha field presence
                EC.presence_of_element_located((By.NAME, "answer"))
            )
            WebDriverWait(self.__driver, 2).until( # captcha image presence
                EC.presence_of_element_located((By.ID, "loadImgId"))
            )
            return True
        except:
            self._showTrace(f"登录页面加载失败 !")
            return False


    def __initDriverUrl(
        self,
    ) -> bool:

        self.__driver.get(self.__system_config_reader.get("library/host_url"))
        if not self.__waitResponseLoad():
            return False
        return True


    def __run(
        self,
        username: str,
        password: str,
        reserve_info: dict,
    ) -> bool:

        success = False

        # login
        if not self.__lib_login.login(
            username,
            password,
            self.__system_config_reader.get("login/max_attempt", 5),
            self.__system_config_reader.get("login/auto_captcha", True),
        ):
            return False
        run_mode = self.__system_config_reader.get("run/mode", 1)
        run_mode = {
            "auto_reserve":  run_mode&0x1,
            "auto_checkin":  run_mode&0x2,
            "auto_renewal":  run_mode&0x4,
        }
        # reserve or checkin or renewal
        """
            Here, we collect the run mode from the config file.
        """
        if self.__lib_reserve.canReserve(reserve_info.get("date")) and run_mode["auto_reserve"]:
            if self.__lib_reserve.reserve(reserve_info):
                self._showTrace(f"用户 {username} 预约成功 !")
                success = True
            else:
                self._showTrace(f"用户 {username} 预约失败 !")
                success = False
        # logout
        if not self.__lib_logout.logout(
            username,
        ):
            self.__driver.get(self.__system_config_reader.get("library/host_url"))
            return False
        return success


    def run(
        self,
        system_config_reader: ConfigReader,
        users_config_reader: ConfigReader,
    ):

        self.__system_config_reader = system_config_reader
        self.__users_config_reader = users_config_reader
        if not self.__initBrowserDriver():
            return
        else:
            if not self.__initDriverUrl():
                return

        user_counter = {"current": 0, "success": 0, "failed": 0}
        users = self.__users_config_reader.get("users")
        self._showTrace(f"共发现 {len(users)} 个用户, "\
            f"用户配置文件路径: {self.__users_config_reader.configPath()}")

        for user in users:
            self._showTrace(f"正在处理第 {user_counter["current"]}/{len(users)} 个用户: {user['username']}......")
            if self.__run(
                username=user["username"],
                password=user["password"],
                reserve_info=user["reserve_info"],
            ):
                user_counter["success"] += 1
            else:
                user_counter["failed"] += 1
        self._showTrace(f"处理完成, 共计 {user_counter["current"]} 个用户, "\
            f"成功 {user_counter["success"]} 个用户, "\
            f"失败 {user_counter["failed"]} 个用户")
        return


    def close(
        self,
    ) -> bool:

        if self.__driver:
            self.__driver.quit()
            self.__driver = None
            self._showTrace(f"浏览器驱动已关闭")
            return True
        else:
            self._showTrace(f"浏览器驱动未初始化，无需关闭")
            return False