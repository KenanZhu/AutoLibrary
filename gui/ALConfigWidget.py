# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os
import sys

from PySide6.QtCore import (
    Qt, Signal, Slot, QTime, QDate, QDir, QFileInfo
)
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QMessageBox, QFileDialog, QListWidgetItem
)
from PySide6.QtGui import QCloseEvent

from .Ui_ALConfigWidget import Ui_ALConfigWidget

from ConfigReader import ConfigReader
from ConfigWriter import ConfigWriter


class ALConfigWidget(QWidget, Ui_ALConfigWidget):

    configWidgetCloseSingal = Signal(dict)

    def __init__(
        self,
        parent = None,
        config_paths = {
            "system":
            f"{QDir.toNativeSeparators(QFileInfo(sys.executable).absoluteDir().absoluteFilePath("system.json"))}",
            "users":
            f"{QDir.toNativeSeparators(QFileInfo(sys.executable).absoluteDir().absoluteFilePath("users.json"))}",
        }
    ):

        super().__init__(parent)

        self.setupUi(self)
        self.connectSignals()
        self.modifyUi()
        self.__config_paths = config_paths
        self.__system_config_data = self.loadSystemConfig(self.__config_paths["system"])
        self.__users_config_data = self.loadUsersConfig(self.__config_paths["users"])
        if not self.__system_config_data:
            self.initlizeDefaultConfig("system")
        if not self.__users_config_data:
            self.initlizeDefaultConfig("users")
        self.initlizeConfigToWidget("system", self.__system_config_data)
        self.initlizeConfigToWidget("users", self.__users_config_data)


    def modifyUi(
        self
    ):

        self.initlizeFloorRoomMap()
        self.initilizeUserInfoWidget()


    def connectSignals(
        self
    ):

        self.ShowPasswordCheckBox.clicked.connect(self.onShowPasswordCheckBoxChecked)
        self.FloorComboBox.currentIndexChanged.connect(self.onFloorComboBoxCurrentIndexChanged)
        self.UserListWidget.currentItemChanged.connect(self.onUserListWidgetCurrentItemChanged)
        self.AddUserButton.clicked.connect(self.onAddUserButtonClicked)
        self.DelUserButton.clicked.connect(self.onDelUserButtonClicked)
        self.BrowseBrowserDriverButton.clicked.connect(self.onBrowseBrowserDriverButtonClicked)
        self.BrowseCurrentSystemConfigButton.clicked.connect(self.onBrowseCurrentSystemConfigButtonClicked)
        self.BrowseCurrentUserConfigButton.clicked.connect(self.onBrowseCurrentUserConfigButtonClicked)
        self.BrowseExportSystemConfigButton.clicked.connect(self.onBrowseExportSystemConfigButtonClicked)
        self.BrowseExportUserConfigButton.clicked.connect(self.onBrowseExportUserConfigButtonClicked)
        self.ExportConfigButton.clicked.connect(self.onExportConfigButtonClicked)
        self.NewConfigButton.clicked.connect(self.onNewConfigButtonClicked)
        self.LoadConfigButton.clicked.connect(self.onLoadConfigButtonClicked)
        self.ConfirmButton.clicked.connect(self.onConfirmButtonClicked)
        self.CancelButton.clicked.connect(self.onCancelButtonClicked)


    def closeEvent(
        self,
        event: QCloseEvent
    ):

        self.configWidgetCloseSingal.emit(self.__config_paths)
        super().closeEvent(event)


    def initlizeFloorRoomMap(
        self
    ):

        self.__floor_map = {
            "2": "二层",
            "3": "三层",
            "4": "四层",
            "5": "五层"
        }
        self.__room_map = {
            "1": "二层内环",
            "2": "二层外环",
            "3": "三层内环",
            "4": "三层外环",
            "5": "四层内环",
            "6": "四层外环",
            "7": "四层期刊区",
            "8": "五层考研"
        }
        self.__floor_rmap = {
            v: k for k, v in self.__floor_map.items()
        }
        self.__room_rmap = {
            v: k for k, v in self.__room_map.items()
        }
        self.__floor_room_map = {
            "二层": ["二层内环", "二层外环"],
            "三层": ["三层内环", "三层外环"],
            "四层": ["四层内环", "四层外环", "四层期刊区"],
            "五层": ["五层考研"]
        }


    def initlizeDefaultConfigPaths(
        self
    ) -> dict:

        script_path = sys.executable
        script_dir = QFileInfo(script_path).absoluteDir()
        return {
            "users": QDir.toNativeSeparators(script_dir.absoluteFilePath("users.json")),
            "system": QDir.toNativeSeparators(script_dir.absoluteFilePath("system.json"))
        }


    def initlizeDefaultConfig(
        self,
        which: str
    ):

        default_config_paths = self.initlizeDefaultConfigPaths()
        if which == "system":
            self.__system_config_data = self.defaultSystemConfig()
            self.__config_paths["system"] = default_config_paths["system"]
            self.saveSystemConfig(self.__config_paths["system"], self.__system_config_data)
        elif which == "users":
            self.__users_config_data = self.defaultUsersConfig()
            self.__config_paths["users"] = default_config_paths["users"]
            self.saveUsersConfig(self.__config_paths["users"], self.__users_config_data)
        if which == "system":
            file_type = "系统配置文件"
        elif which == "users":
            file_type = "用户配置文件"
        QMessageBox.information(
            self,
            "提示 - AutoLibrary",
            f"{file_type}已初始化, \n"\
            f" 文件路径: {self.__config_paths[which]}"
        )


    def initlizeConfigToWidget(
        self,
        which: str,
        config_data: dict
    ):

        if which == "system":
            self.setSystemConfigToWidget(config_data)
            self.CurrentSystemConfigEdit.setText(self.__config_paths["system"])
        elif which == "users":
            self.initilizeUserInfoWidget()
            self.fillUsersList(config_data)
            self.CurrentUserConfigEdit.setText(self.__config_paths["users"])


    def defaultSystemConfig(
        self
    ) -> dict:

        return {
            "library": {
                "host_url": "http://10.1.20.7",
                "login_url": "/login"
            },
            "login": {
                "auto_captcha": True,
                "max_attempt": 3
            },
            "web_driver": {
                "driver_type": "edge",
                "driver_path": "msedgedriver.exe",
                "headless": False
            },
            "mode": {
                "run_mode": 1
            }
        }


    def defaultUsersConfig(
        self
    ) -> dict:

        return {
            "users": []
        }


    def collectSystemConfigFromWidget(
        self
    ) -> dict:

        system_config = self.defaultSystemConfig()
        # library config is never changed
        system_config["login"]["auto_captcha"] = self.AutoCaptchaCheckBox.isChecked()
        system_config["login"]["max_attempt"] = self.LoginAttemptSpinBox.value()
        system_config["web_driver"]["driver_type"] = self.BrowserTypeComboBox.currentText()
        system_config["web_driver"]["driver_path"] = self.BrowseBrowserDriverEdit.text()
        system_config["web_driver"]["headless"] = self.HeadlessCheckBox.isChecked()
        run_mode = 0
        if self.AutoReserveCheckBox.isChecked():
            run_mode |= 0x01
        if self.AutoCheckinCheckBox.isChecked():
            run_mode |= 0x02
        if self.AutoRenewalCheckBox.isChecked():
            run_mode |= 0x04
        system_config["mode"]["run_mode"] = run_mode
        return system_config


    def setSystemConfigToWidget(
        self,
        system_config: dict
    ):

        self.HostUrlEdit.setText(system_config["library"]["host_url"])
        self.LoginUrlEdit.setText(system_config["library"]["login_url"])
        self.AutoCaptchaCheckBox.setChecked(system_config["login"]["auto_captcha"])
        self.LoginAttemptSpinBox.setValue(system_config["login"]["max_attempt"])
        self.BrowserTypeComboBox.setCurrentText(system_config["web_driver"]["driver_type"])
        driver_path = os.path.abspath(system_config["web_driver"]["driver_path"])
        self.BrowseBrowserDriverEdit.setText(QDir.toNativeSeparators(driver_path))
        self.HeadlessCheckBox.setChecked(system_config["web_driver"]["headless"])
        run_mode = system_config["mode"]["run_mode"]
        self.AutoReserveCheckBox.setChecked(run_mode&0x01)
        self.AutoCheckinCheckBox.setChecked(run_mode&0x02)
        self.AutoRenewalCheckBox.setChecked(run_mode&0x04)


    def initilizeUserInfoWidget(
        self
    ):

        self.UsernameEdit.setText("")
        self.PasswordEdit.setText("")
        self.UserListWidget.setSortingEnabled(True)
        self.PasswordEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.ShowPasswordCheckBox.setChecked(False)
        self.FloorComboBox.setCurrentIndex(0)
        self.onFloorComboBoxCurrentIndexChanged()
        self.DateEdit.setDate(QDate.currentDate())
        self.DateEdit.setMinimumDate(QDate.currentDate())
        self.BeginTimeEdit.setTime(QTime.currentTime())
        self.PreferEarlyBeginTimeCheckBox.setChecked(False)
        self.MaxBeginTimeDiffSpinBox.setValue(30)
        self.EndTimeEdit.setTime(QTime.currentTime().addSecs(120*60))
        self.PreferLateEndTimeCheckBox.setChecked(False)
        self.MaxEndTimeDiffSpinBox.setValue(30)
        self.ExpectDurationSpinBox.setValue(self.BeginTimeEdit.time().secsTo(self.EndTimeEdit.time())/3600)
        self.SatisfyDurationCheckBox.setChecked(False)


    def collectUserConfigFromUserInfoWidget(
        self
    ) -> dict:

        user_config = {
            "username": self.UsernameEdit.text(),
            "password": self.PasswordEdit.text(),
            "reserve_info": {
                "begin_time":{},
                "end_time": {}
            }
        }
        user_config["reserve_info"]["date"] = self.DateEdit.dateTime().toString("yyyy-MM-dd")
        user_config["reserve_info"]["place"] = self.PlaceComboBox.currentText()
        user_config["reserve_info"]["floor"] = self.__floor_rmap[self.FloorComboBox.currentText()]
        user_config["reserve_info"]["room"] = self.__room_rmap[self.RoomComboBox.currentText()]
        user_config["reserve_info"]["seat_id"] = self.SeatIDEdit.text()
        user_config["reserve_info"]["begin_time"]["time"] = self.BeginTimeEdit.time().toString("HH:mm")
        user_config["reserve_info"]["begin_time"]["max_diff"] = self.MaxBeginTimeDiffSpinBox.value()
        user_config["reserve_info"]["begin_time"]["prefer_early"] = self.PreferEarlyBeginTimeCheckBox.isChecked()
        user_config["reserve_info"]["end_time"]["time"] = self.EndTimeEdit.time().toString("HH:mm")
        user_config["reserve_info"]["end_time"]["max_diff"] = self.MaxEndTimeDiffSpinBox.value()
        user_config["reserve_info"]["end_time"]["prefer_early"] = not self.PreferLateEndTimeCheckBox.isChecked()
        user_config["reserve_info"]["expect_duration"] = self.ExpectDurationSpinBox.value()
        user_config["reserve_info"]["satisfy_duration"] = self.SatisfyDurationCheckBox.isChecked()
        return user_config


    def collectUserConfigFromUserListWidget(
        self,
        index: int
    ) -> dict:

        user_config = self.defaultUsersConfig()
        if index < 0 or index >= self.UserListWidget.count():
            return user_config
        user_item = self.UserListWidget.item(index)
        if user_item:
            user_config = user_item.data(Qt.UserRole)
        return user_config


    def setUserConfigToWidget(
        self,
        user_config: dict
    ) -> None:

        try:
            self.UsernameEdit.setText(user_config["username"])
            self.PasswordEdit.setText(user_config["password"])
            self.DateEdit.setDate(QDate.fromString(user_config["reserve_info"]["date"], "yyyy-MM-dd"))
            self.PlaceComboBox.setCurrentText(user_config["reserve_info"]["place"])
            self.FloorComboBox.setCurrentText(self.__floor_map[user_config["reserve_info"]["floor"]])
            self.RoomComboBox.setCurrentText(self.__room_map[user_config["reserve_info"]["room"]])
            self.SeatIDEdit.setText(user_config["reserve_info"]["seat_id"])
            self.BeginTimeEdit.setTime(QTime.fromString(user_config["reserve_info"]["begin_time"]["time"], "H:mm"))
            self.MaxBeginTimeDiffSpinBox.setValue(user_config["reserve_info"]["begin_time"]["max_diff"])
            self.PreferEarlyBeginTimeCheckBox.setChecked(user_config["reserve_info"]["begin_time"]["prefer_early"])
            self.EndTimeEdit.setTime(QTime.fromString(user_config["reserve_info"]["end_time"]["time"], "H:mm"))
            self.MaxEndTimeDiffSpinBox.setValue(user_config["reserve_info"]["end_time"]["max_diff"])
            self.PreferLateEndTimeCheckBox.setChecked(not user_config["reserve_info"]["end_time"]["prefer_early"])
            self.ExpectDurationSpinBox.setValue(user_config["reserve_info"]["expect_duration"])
            self.SatisfyDurationCheckBox.setChecked(user_config["reserve_info"]["satisfy_duration"])
        except:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                "用户配置文件读取发生错误 !\n"\
                f"用户: {user_config['username']} 配置文件可能已损坏"
            )


    def loadSystemConfig(
        self,
        system_config_path: str
    ) -> dict:

        try:
            if not system_config_path or not os.path.exists(system_config_path):
                raise Exception("文件路径不存在")
            system_config = ConfigReader(system_config_path).getConfigs()
            if system_config and "library" in system_config\
                and "web_driver" in system_config\
                and "login" in system_config:
                return system_config
            return None
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"系统配置文件读取发生错误 ! : {e}\n"\
                f"文件路径: {system_config_path}"
            )
            return None


    def saveSystemConfig(
        self,
        system_config_path: str,
        system_config_data: dict
    ) -> bool:

        try:
            if not system_config_path:
                raise Exception("文件路径为空")
            if not system_config_data or not isinstance(system_config_data, dict):
                raise Exception("系统配置数据为空或类型错误")
            ConfigWriter(system_config_path, system_config_data)
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"配置文件写入发生错误 ! : {e}\n"\
                f"文件路径: {system_config_path}"
            )
            return False


    def loadUsersConfig(
        self,
        users_config_path: str
    ) -> dict:

        try:
            if not users_config_path or not os.path.exists(users_config_path):
                raise Exception("文件路径不存在")
            users_config = ConfigReader(users_config_path).getConfigs()
            if users_config and "users" in users_config:
                return users_config
            return None
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取发生错误 ! : {e}\n"\
                f"文件路径: {users_config_path}"
            )
            return None


    def saveUsersConfig(
        self,
        users_config_path: str,
        users_config_data: dict
    ) -> bool:

        try:
            if not users_config_path:
                raise Exception("文件路径为空")
            if not users_config_data or not isinstance(users_config_data, dict):
                raise Exception("用户配置数据为空或类型错误")
            ConfigWriter(users_config_path, users_config_data)
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件写入发生错误 ! : {e}\n"\
                f"文件路径: \n{users_config_path}"
            )
            return False


    def saveConfigs(
        self,
        system_config_path: str,
        users_config_path: str
    ) -> bool:

        if users_config_path:
            self.__users_config_data = self.defaultUsersConfig()
            for index in range(self.UserListWidget.count()):
                user_config = self.collectUserConfigFromUserListWidget(index)
                if user_config:
                    self.__users_config_data["users"].append(user_config)
            if not self.saveUsersConfig(
                users_config_path,
                self.__users_config_data
            ):
                return False
        if system_config_path:
            self.__system_config_data = self.collectSystemConfigFromWidget()
            if not self.saveSystemConfig(
                system_config_path,
                self.__system_config_data
            ):
                return False
        return True


    def loadConfig(
        self,
        config_path: str
    ) -> bool:

        if not config_path:
            config_path = QFileDialog.getOpenFileName(
                self,
                "从现有配置文件中加载 - AutoLibrary",
                f"{QDir.toNativeSeparators(QDir.currentPath())}",
                "JSON 文件 (*.json);;所有文件 (*)"
            )[0]
            if not config_path:
                return False
        try:
            system_config = self.loadSystemConfig(config_path)
            users_config = self.loadUsersConfig(config_path)
            if system_config is not None:
                self.__system_config_data.update(system_config)
                self.setSystemConfigToWidget(self.__system_config_data)
                return True
            if users_config is not None:
                self.__users_config_data.update(users_config)
                self.fillUsersList(self.__users_config_data)
                return True
        except:
            return False


    def fillUsersList(
        self,
        users_config_data: list[dict]
    ):

        self.UserListWidget.clear()
        if "users" in users_config_data:
            for user in users_config_data["users"]:
                user_item = QListWidgetItem(user["username"])
                user_item.setData(Qt.UserRole, user)
                self.UserListWidget.addItem(user_item)


    def addUser(
        self
    ):

        new_user = {
            "username": f"新用户-{self.UserListWidget.count()}",
            "password": "000000",
            "reserve_info": {
                "date": f"{QDate.currentDate().toString("yyyy-MM-dd")}",
                "place": "\u56fe\u4e66\u9986",
                "floor": "2",
                "room": "1",
                "seat_id": "",
                "begin_time": {
                    "time": f"{QTime.currentTime().toString("hh:mm")}",
                    "max_diff": 30,
                    "prefer_early": False
                },
                "end_time": {
                    "time": f"{QTime.currentTime().addSecs(2*3600).toString("hh:mm")}",
                    "max_diff": 30,
                    "prefer_early": True
                },
                "expect_duration": 2.0,
                "satisfy_duration": False
            }
        }
        user_item = QListWidgetItem(new_user["username"])
        user_item.setData(Qt.UserRole, new_user)
        self.UserListWidget.addItem(user_item)
        self.UserListWidget.setCurrentItem(user_item)
        self.setUserConfigToWidget(new_user)


    def delUser(
        self
    ):

        current_item = self.UserListWidget.currentItem()
        if current_item:
            self.UserListWidget.takeItem(self.UserListWidget.row(current_item))
            self.UserListWidget.setCurrentItem(None)

    @Slot()
    def onShowPasswordCheckBoxChecked(
        self,
        checked: bool
    ):

        if checked:
            self.PasswordEdit.setEchoMode(QLineEdit.Normal)
        else:
            self.PasswordEdit.setEchoMode(QLineEdit.Password)

    @Slot()
    def onFloorComboBoxCurrentIndexChanged(
        self
    ):

        floor = self.FloorComboBox.currentText()
        self.RoomComboBox.clear()
        self.RoomComboBox.addItems(self.__floor_room_map[floor])
        self.RoomComboBox.setCurrentIndex(0)

    @Slot()
    def onUserListWidgetCurrentItemChanged(
        self,
        current: QListWidgetItem,
        previous: QListWidgetItem
    ):
        # dont care about the 'self.__users_config_data', we already
        # cant effectively update the data of each user, due to the
        # possiblity of frequency edit. we just let the QListWidget
        # help us.
        if not current:
            self.initilizeUserInfoWidget()
            return
        if previous:
            user = self.collectUserConfigFromUserInfoWidget()
            if user:
                previous.setText(user["username"])
                previous.setData(Qt.UserRole, user)
        user = current.data(Qt.UserRole)
        if user:
            self.setUserConfigToWidget(user)

    @Slot()
    def onAddUserButtonClicked(
        self
    ):

        self.addUser()

    @Slot()
    def onDelUserButtonClicked(
        self
    ):

        self.delUser()

    @Slot()
    def onBrowseBrowserDriverButtonClicked(
        self
    ):

        browser_driver_path = QFileDialog.getOpenFileName(
            self,
            "选择浏览器驱动 - AutoLibrary",
            self.BrowseBrowserDriverEdit.text(),
            "可执行文件 (*.exe);;所有文件 (*)"
        )[0]
        if browser_driver_path:
            self.BrowseBrowserDriverEdit.setText(QDir.toNativeSeparators(browser_driver_path))

    @Slot()
    def onBrowseCurrentSystemConfigButtonClicked(
        self
    ):

        system_config_path = QFileDialog.getOpenFileName(
            self,
            "选择其它的系统配置 - AutoLibrary",
            self.CurrentSystemConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if system_config_path:
            system_config_path = QDir.toNativeSeparators(system_config_path)
            if self.loadConfig(system_config_path):
                self.__config_paths["system"] = system_config_path
                self.CurrentSystemConfigEdit.setText(system_config_path)

    @Slot()
    def onBrowseCurrentUserConfigButtonClicked(
        self
    ):

        users_config_path = QFileDialog.getOpenFileName(
            self,
            "选择其它的用户配置 - AutoLibrary",
            self.CurrentUserConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if users_config_path:
            users_config_path = QDir.toNativeSeparators(users_config_path)
            if self.loadConfig(users_config_path):
                self.__config_paths["users"] = users_config_path
                self.CurrentUserConfigEdit.setText(users_config_path)

    @Slot()
    def onBrowseExportSystemConfigButtonClicked(
        self
    ):

        system_config_path = QFileDialog.getSaveFileName(
            self,
            "导出系统配置 - AutoLibrary",
            self.CurrentSystemConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if system_config_path:
            self.ExportSystemConfigEdit.setText(QDir.toNativeSeparators(system_config_path))

    @Slot()
    def onBrowseExportUserConfigButtonClicked(
        self
    ):

        users_config_path = QFileDialog.getSaveFileName(
            self,
            "导出用户配置 - AutoLibrary",
            self.CurrentUserConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if users_config_path:
            self.ExportUserConfigEdit.setText(QDir.toNativeSeparators(users_config_path))

    @Slot()
    def onExportConfigButtonClicked(
        self
    ):

        msg = ""

        system_config_path = self.ExportSystemConfigEdit.text()
        users_config_path = self.ExportUserConfigEdit.text()
        if system_config_path:
            if self.saveConfigs(
                system_config_path, ""
            ):
                msg += f"系统配置文件已导出到: \n'{system_config_path}'\n"
            else:
                msg += f"系统配置文件导出失败: \n'{system_config_path}'\n"
        if users_config_path:
            if self.saveConfigs(
                "", users_config_path
            ):
                msg += f"用户配置文件已导出到: \n'{users_config_path}'\n"
        if msg:
            QMessageBox.information(
                self,
                "提示 - AutoLibrary",
                msg
            )

    @Slot()
    def onLoadConfigButtonClicked(
        self
    ):

        self.loadConfig("")

    @Slot()
    def onNewConfigButtonClicked(
        self
    ):

        file_path = self.CurrentSystemConfigEdit.text()
        folder_dir = QFileDialog.getExistingDirectory(
            self,
            "选择新建配置的文件夹 - AutoLibrary",
            QDir.toNativeSeparators(QFileInfo(os.path.abspath(file_path)).absoluteDir().path())
        )
        if not folder_dir:
            return
        system_config_path = QDir.toNativeSeparators(os.path.join(folder_dir, "system.json"))
        users_config_path = QDir.toNativeSeparators(os.path.join(folder_dir, "users.json"))
        system_exists = os.path.isfile(system_config_path)
        users_exists = os.path.isfile(users_config_path)
        if system_exists or users_exists:
            exist_files = []
            if system_exists:
                exist_files.append(system_config_path)
            if users_exists:
                exist_files.append(users_config_path)
            reply = QMessageBox.information(
                self,
                "信息 - AutoLibrary",
                f"文件夹中已存在以下文件, 是否覆盖 ?\n{chr(10).join(exist_files)}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.__system_config_data = self.defaultSystemConfig()
        self.__users_config_data = self.defaultUsersConfig()
        self.__config_paths = {
            "system": system_config_path,
            "users": users_config_path
        }
        self.initlizeConfigToWidget("system", self.__system_config_data)
        self.initlizeConfigToWidget("users", self.__users_config_data)

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        if self.UserListWidget.currentItem() is not None:
            user = self.collectUserConfigFromUserInfoWidget()
            if user:
                self.UserListWidget.currentItem().setData(Qt.UserRole, user)
        if self.saveConfigs(
            self.__config_paths["system"],
            self.__config_paths["users"]
        ):
            QMessageBox.information(
                self,
                "信息 - AutoLibrary",
                "配置文件保存成功 !\n"
                f"系统配置文件路径: \n{self.__config_paths['system']}\n"\
                f"用户配置文件路径: \n{self.__config_paths['users']}"
            )
        else:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                "配置文件保存失败, 请检查文件路径权限"
            )
        self.close()

    @Slot()
    def onCancelButtonClicked(
        self
    ):

        self.close()
