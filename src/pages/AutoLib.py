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
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import (
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from base.MsgBase import MsgBase
from pages.LoginPage import LoginPage
from pages.MainShell import MainShell
from pages.flows.ReserveFlow import ReserveFlow, ReserveContext
from pages.flows.CheckinFlow import CheckinFlow
from pages.flows.RenewFlow import RenewFlow
from pages.services.CaptchaSolver import CaptchaSolver
from pages.services.ReserveChecker import ReserveChecker
from pages.services.RecordChecker import RecordChecker


class AutoLib(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
        run_config: dict,
    ) -> None:

        super().__init__(input_queue, output_queue)
        self.__run_config: dict = run_config
        self.__user_config: dict | None = None
        self.__driver: WebDriver | None = None
        self.__driver_type: str = ""
        self.__driver_path: str = ""
        self.__login_page: LoginPage = None
        self.__shell: MainShell = None
        self.__captcha_solver: CaptchaSolver = None
        self.__record_checker: RecordChecker = None
        self.__reserve_checker: ReserveChecker = None
        self.__reserve_flow: ReserveFlow = None
        self.__checkin_flow: CheckinFlow = None
        self.__renew_flow: RenewFlow = None

        if not self.__initBrowserDriver():
            raise Exception("浏览器驱动初始化失败 !")
        else:
            if not self.__initDriverUrl():
                self.close()
                raise Exception("浏览器驱动 URL 初始化失败 !")
            self.__initPagesServices()
            self.__initPagesFlows()

    def __initBrowserDriver(
        self,
    ) -> bool:

        self._showTrace("正在初始化浏览器驱动......", no_log=True)
        driver_config: dict = self.__run_config.get("web_driver", None)
        self.__driver_type = driver_config.get("driver_type", "none")
        self.__driver_type = self.__driver_type.lower()
        match self.__driver_type:
            case "edge":
                driver_options = webdriver.EdgeOptions()
            case "chrome":
                driver_options = webdriver.ChromeOptions()
            case "firefox":
                driver_options = webdriver.FirefoxOptions()
            case _:
                self._showTrace(
                    f"不支持的浏览器驱动类型: {self.__driver_type} !",
                    self.TraceLevel.WARNING,
                )
                return False
        if not driver_config:
            self._showTrace("未配置浏览器驱动参数 !", self.TraceLevel.ERROR)
            return False
        if driver_config.get("headless", False):
            driver_options.add_argument("--headless")
            driver_options.add_argument("--disable-gpu")
            driver_options.add_argument("--no-sandbox")
            driver_options.add_argument("--disable-dev-shm-usage")

        # must be 1920x1080, otherwise the page will cause some elements not accessible
        driver_options.add_argument("--window-size=1920,1080")

        # omit ssl errors and verbose log level
        driver_options.add_argument("--ignore-certificate-errors")
        driver_options.add_argument("--ignore-ssl-errors")
        driver_options.add_argument("--log-level=OFF")
        driver_options.add_argument("--silent")

        # set options for chrome and edge
        if self.__driver_type.lower() in ["edge", "chrome"]:
            driver_options.add_argument("--remote-allow-origins=*")
            driver_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            driver_options.add_experimental_option("useAutomationExtension", False)
            driver_options.add_argument("--disable-blink-features=AutomationControlled")
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "\
                         "AppleWebKit/537.36 (KHTML, like Gecko) "\
                         "Chrome/120.0.0.0 "\
                         "Safari/537.36"
            if self.__driver_type == "edge":
                user_agent += " Edg/120.0.0.0"

        # set options for firefox
        elif self.__driver_type == "firefox":
            driver_options.set_preference("dom.webdriver.enabled", False)
            driver_options.set_preference("useAutomationExtension", False)
            user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) "\
                         "Gecko/20100101 Firefox/120.0"
        driver_options.add_argument(f"user-agent={user_agent}")

        # init browser driver
        self.__driver_path = driver_config.get("driver_path", "")
        if not self.__driver_path:
            self._showTrace("未配置浏览器驱动路径 !", self.TraceLevel.WARNING)
            return False
        try:
            self.__driver_path = os.path.abspath(self.__driver_path)
            service = None
            match self.__driver_type:
                case "edge":
                    service = EdgeService(executable_path=self.__driver_path)
                    self.__driver = webdriver.Edge(service=service, options=driver_options)
                case "chrome":
                    service = ChromeService(executable_path=self.__driver_path)
                    self.__driver = webdriver.Chrome(service=service, options=driver_options)
                case "firefox":
                    self._showTrace("Firefox 浏览器驱动初始化略慢, 请耐心等待...", no_log=True)
                    service = FirefoxService(executable_path=self.__driver_path)
                    self.__driver = webdriver.Firefox(service=service, options=driver_options)
                case _:
                    raise Exception(f"不支持的浏览器驱动类型: {self.__driver_type} !")
            self.__driver.implicitly_wait(1)
            self.__driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
        except WebDriverException as e:
            self._showTrace(f"浏览器驱动初始化失败: {e}", self.TraceLevel.ERROR)
            return False
        self._showTrace(f"浏览器驱动已初始化, 类型: {self.__driver_type}, 路径: {self.__driver_path}")
        return True

    def __initDriverUrl(
        self,
    ) -> bool:

        lib_config: dict = self.__run_config.get("library", None)
        if not lib_config:
            self._showTrace("未配置图书馆参数 !", self.TraceLevel.ERROR)
            return False
        url: str = lib_config.get("host_url") + lib_config.get("login_url")
        self.__login_page = LoginPage(self._input_queue, self._output_queue, self.__driver)
        self.__driver.set_page_load_timeout(5)
        try:
            self.__driver.get(url)
        except TimeoutException:
            self.__login_page.stopPageLoad()
            self._showTrace(
                "图书馆登录页面加载超时 ! 请检查网络环境是否正常", self.TraceLevel.ERROR
            )
            return False
        except WebDriverException as e:
            self._showTrace(f"图书馆页面加载失败: {e}", self.TraceLevel.ERROR)
            return False
        if not self.__login_page.waitUntilLoaded():
            return False
        return True

    def __initPagesServices(
        self,
    ) -> None:

        if not self.__driver:
            self._showTrace("浏览器驱动未初始化, 请先初始化浏览器驱动 !", self.TraceLevel.WARNING)
            return
        self.__shell = MainShell(self.__driver)
        self.__captcha_solver = CaptchaSolver(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
        )
        self.__record_checker = RecordChecker(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
        )
        self.__reserve_checker = ReserveChecker(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
        )

    def __initPagesFlows(
        self,
    ) -> None:

        self.__reserve_flow = ReserveFlow(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
            driver=self.__driver,
            shell=self.__shell,
        )
        self.__checkin_flow = CheckinFlow(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
            driver=self.__driver,
            shell=self.__shell,
        )
        self.__renew_flow = RenewFlow(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
            driver=self.__driver,
            shell=self.__shell,
        )

    def __run(
        self,
        username: str,
        password: str,
        login_config: dict,
        run_mode_config: dict,
        reserve_info: dict,
    ) -> int:

        # result : -1 - terminate, 0 - success, 1 - failed, 2 - passed
        result: int = 2

        # login
        auto_captcha: bool = login_config.get("auto_captcha", True)
        if not self.__login_page.login(
            username,
            password,
            captcha_solver=self.__captcha_solver.solveCaptcha,
            auto_captcha=auto_captcha,
            max_attempts=login_config.get("max_attempt", 3),
        ):
            return 1
        run_mode_raw: int = run_mode_config.get("run_mode", 0)
        run_mode: dict[str, bool] = {
            "auto_reserve": run_mode_raw & 0x1,
            "auto_checkin": run_mode_raw & 0x2,
            "auto_renewal": run_mode_raw & 0x4,
        }

        # reserve
        if run_mode["auto_reserve"]:
            if self.__reserve_checker.check(reserve_info):
                if self.__record_checker.canReserve(self.__shell, reserve_info["date"]):
                    ctx = ReserveContext(
                        username=username,
                        date=reserve_info["date"],
                        floor=reserve_info["floor"],
                        room=reserve_info["room"],
                        seat_id=reserve_info["seat_id"],
                        begin_time=reserve_info["begin_time"]["time"],
                        end_time=reserve_info["end_time"]["time"],
                        begin_max_diff=reserve_info["begin_time"]["max_diff"],
                        end_max_diff=reserve_info["end_time"]["max_diff"],
                        begin_prefer_early=reserve_info["begin_time"]["prefer_early"],
                        end_prefer_early=reserve_info["end_time"]["prefer_early"],
                        expect_duration=reserve_info["expect_duration"],
                        satisfy_duration=reserve_info["satisfy_duration"],
                    )
                    if self.__reserve_flow.execute(ctx):
                        result = 0
                    else:
                        result = 1
                else:
                    self._showTrace(f"用户 {username} 无法预约, 已跳过")
                    result = 2
            else:
                result = 1

        # checkin
        last_result: int = result
        if run_mode["auto_checkin"] and last_result != 1:
            if self.__record_checker.canCheckin(self.__shell):
                if self.__checkin_flow.execute(username):
                    result = 0
                else:
                    result = 1
            else:
                self._showTrace(f"用户 {username} 无法签到, 已跳过")
                result = 2
        if last_result == 0:  # partly success
            result = 0

        # renewal
        last_result = result
        if run_mode["auto_renewal"] and last_result != 1:
            can_renew, record = self.__record_checker.canRenew(self.__shell)
            if can_renew:
                renew_info: dict = reserve_info.get("renew_time", {})
                if self.__renew_flow.execute(username, record, renew_info):
                    if self.__record_checker.postRenewCheck(self.__shell, record):
                        self._showTrace(f"用户 {username} 续约成功 !")
                        result = 0
                    else:
                        if result != 1:  # partly success
                            result = 0
                        else:
                            result = 1
                else:
                    result = 1
            else:
                self._showTrace(f"用户 {username} 无法续约, 已跳过")
                result = 2
        if last_result == 0:  # partly success
            result = 0

        # logout
        if not self.__shell.logout():
            self._showTrace(f"用户 {username} 退出登录失败, 尝试直接重载页面")
            if not self.__initDriverUrl():
                self._showTrace(f"用户 {username} 重载页面失败, 无法继续操作, 该任务已终止 !")
                return -1
        self._showTrace(f"用户 {username} 已退出登录")
        return result

    def run(
        self,
        user_config: dict,
    ) -> None:

        self.__user_config = user_config
        user_counter: dict[str, int] = {"current": 0, "success": 0, "failed": 0, "passed": 0}
        users: list = self.__user_config.get("users", [])
        self._showTrace(f"共发现 {len(users)} 个用户")
        for user in users:
            user_counter["current"] += 1
            self._showTrace(
                f"正在处理第 {user_counter["current"]}/{len(users)} 个用户: {user.get("username", "未知")}......",
                no_log=True,
            )
            if not user.get("enabled", False):
                self._showTrace(f"用户 {user.get("username", "未知")} 已跳过")
                user_counter["passed"] += 1
                continue
            r: int = self.__run(
                username=user.get("username", ""),
                password=user.get("password", ""),
                login_config=self.__run_config.get("login", {}),
                run_mode_config=self.__run_config.get("mode", {}),
                reserve_info=user.get("reserve_info", {}),
            )
            if r == -1:
                self._showTrace(
                    f"用户 {user.get("username", "未知")} 处理过程中页面发生异常, 无法继续操作, 任务已终止 !",
                    self.TraceLevel.WARNING,
                )
                break
            elif r == 0:
                user_counter["success"] += 1
            elif r == 1:
                user_counter["failed"] += 1
            elif r == 2:
                user_counter["passed"] += 1
        self._showTrace(
            f"处理完成, 共计 {user_counter["current"]} 个用户, "
            f"成功 {user_counter["success"]} 个用户, "
            f"失败 {user_counter["failed"]} 个用户, "
            f"跳过 {user_counter["passed"]} 个用户"
        )
        return

    def close(
        self,
    ) -> bool:

        if self.__driver:
            if self.__driver_type.lower() == "firefox":
                self._showTrace(
                    "Firefox 浏览器驱动关闭略慢, 请耐心等待...",
                    no_log=True,
                )
            try:
                self.__driver.quit()
            except WebDriverException as e:
                self._showTrace(f"浏览器驱动关闭时发生异常: {e}", self.TraceLevel.WARNING)
            self.__driver = None
            self._showTrace("浏览器驱动已关闭")
            return True
        else:
            self._showTrace("浏览器驱动未初始化, 无需关闭", no_log=True)
            return False
