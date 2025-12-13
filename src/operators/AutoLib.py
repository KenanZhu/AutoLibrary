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

from base.MsgBase import MsgBase
from operators.LibChecker import LibChecker
from operators.LibLogin import LibLogin
from operators.LibLogout import LibLogout
from operators.LibReserve import LibReserve
from operators.LibCheckin import LibCheckin
from operators.LibRenew import LibRenew

from utils.ConfigReader import ConfigReader


class AutoLib(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        run_config: dict
    ):
        super().__init__(input_queue, output_queue)

        self.__run_config = run_config
        self.__user_config = None
        self.__driver = None
        if not self.__initBrowserDriver():
            raise Exception("浏览器驱动初始化失败")
        else:
            if not self.__initDriverUrl():
                raise Exception("浏览器驱动URL初始化失败")
            self.__initLibOperators()


    def __initBrowserDriver(
        self
    ) -> bool:

        self._showTrace("正在初始化浏览器驱动......")
        edge_options = webdriver.EdgeOptions()

        web_driver_config = self.__run_config.get("web_driver", None)
        if not web_driver_config:
            self._showTrace("未配置浏览器驱动参数 !")
            return False
        if web_driver_config.get("headless"):
            edge_options.add_argument("--headless")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")

        # must be 1920x1080, otherwise the page will cause some elements not accessible
        edge_options.add_argument("--window-size=1920,1080")
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
        self.__driver_path = web_driver_config.get("driver_path")
        self.__driver_type = web_driver_config.get("driver_type")
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
            self.__driver.implicitly_wait(1)
            self.__driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except Exception as e:
            self._showTrace(f"浏览器驱动初始化失败: {e}")
            return False
        self._showTrace(f"浏览器驱动已初始化, 类型: {self.__driver_type}, 路径: {self.__driver_path}")
        return True


    def __initLibOperators(
        self
    ):

        if not self.__driver:
            self._showTrace(f"浏览器驱动未初始化, 请先初始化浏览器驱动 !")
            return
        self.__lib_checker = LibChecker(self._input_queue, self._output_queue, self.__driver)
        self.__lib_login = LibLogin(self._input_queue, self._output_queue, self.__driver)
        self.__lib_logout = LibLogout(self._input_queue, self._output_queue, self.__driver)
        self.__lib_reserve = LibReserve(self._input_queue, self._output_queue, self.__driver)
        self.__lib_checkin = LibCheckin(self._input_queue, self._output_queue, self.__driver)
        self.__lib_renew = LibRenew(self._input_queue, self._output_queue, self.__driver)


    def __waitResponseLoad(
        self
    ) -> bool:

        # wait for page load
        try:
            WebDriverWait(self.__driver, 2).until( # title contains "首页"
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

        lib_config = self.__run_config.get("library", None)
        if not lib_config:
            self._showError("未配置图书馆参数 !")
            return False
        url = lib_config.get("host_url") + lib_config.get("login_url")
        self.__driver.get(url)
        if not self.__waitResponseLoad():
            return False
        return True


    def __run(
        self,
        username: str,
        password: str,
        login_config: dict,
        run_mode_config: dict,
        reserve_info: dict
    ) -> int:

        # result : -1 - terminate, 0 - success, 1 - failed, 2 - passed
        result = 2

        # login
        if not self.__lib_login.login(
            username,
            password,
            login_config.get("max_attempt", 3),
            login_config.get("auto_captcha", True),
        ):
            return 1
        """
            Here, we collect the run mode from the run config.
        """
        run_mode = run_mode_config.get("run_mode", 0)
        run_mode = {
            "auto_reserve": run_mode&0x1,
            "auto_checkin": run_mode&0x2,
            "auto_renewal": run_mode&0x4,
        }
        # reserve
        if run_mode["auto_reserve"]:
            if self.__lib_checker.canReserve(reserve_info.get("date")):
                if self.__lib_reserve.reserve(username, reserve_info):
                    result = 0
                else:
                    result = 1
            else:
                self._showTrace(f"用户 {username} 无法预约，已跳过")
                result = 2
        # checkin
        if run_mode["auto_checkin"] and result == 2:
            if self.__lib_checker.canCheckin():
                if self.__lib_checkin.checkin(username):
                    result = 0
                else:
                    result = 1
            else:
                self._showTrace(f"用户 {username} 无法签到，已跳过")
                result = 2
        # renewal
        if run_mode["auto_renewal"] and result == 2:
            if record := self.__lib_checker.canRenew():
                if self.__lib_renew.renew(username, record, reserve_info):
                    if self.__lib_checker.postRenewCheck(record):
                        result = 0
                    else:
                        result = 1
                else:
                    result = 1
            else:
                self._showTrace(f"用户 {username} 无法续约，已跳过")
                result = 2
        # logout
        if not self.__lib_logout.logout(
            username
        ):
            # if logout is failed, we must make sure the host to be reloaded
            # otherwise, the next login may fail
            if not self.__initDriverUrl():
                return -1
        return result


    def run(
        self,
        user_config: dict
    ):

        self.__user_config = user_config

        user_counter = {"current": 0, "success": 0, "failed": 0, "passed": 0}
        users = self.__user_config["users"]
        self._showTrace(f"共发现 {len(users)} 个用户")
        for user in users:
            user_counter["current"] += 1
            self._showTrace(
                f"正在处理第 {user_counter["current"]}/{len(users)} 个用户: {user["username"]}......"
            )
            if not user["enabled"]:
                self._showTrace(f"用户 {user["username"]} 已跳过")
                user_counter["passed"] += 1
                continue
            r = self.__run(
                username=user["username"],
                password=user["password"],
                login_config=self.__run_config["login"],
                run_mode_config=self.__run_config["mode"],
                reserve_info=user["reserve_info"],
            )
            if r == -1:
                self._showTrace(
                    f"用户 {user["username"]} 处理过程中页面发生异常，无法继续操作, 任务已终止 !"
                )
                break
            elif r == 0:
                user_counter["success"] += 1
            elif r == 1:
                user_counter["failed"] += 1
            elif r == 2:
                user_counter["passed"] += 1
        self._showTrace(f"处理完成, 共计 {user_counter["current"]} 个用户, "\
            f"成功 {user_counter["success"]} 个用户, "\
            f"失败 {user_counter["failed"]} 个用户, "\
            f"跳过 {user_counter["passed"]} 个用户"
        )
        return


    def close(
        self
    ) -> bool:

        if self.__driver:
            self.__driver.quit()
            self.__driver = None
            self._showTrace(f"浏览器驱动已关闭")
            return True
        else:
            self._showTrace(f"浏览器驱动未初始化, 无需关闭")
            return False