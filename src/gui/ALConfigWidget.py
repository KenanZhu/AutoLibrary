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
    QWidget, QLineEdit, QMessageBox, QFileDialog,
    QTreeWidgetItem, QMenu, QInputDialog
)
from PySide6.QtGui import (
     QCloseEvent, QAction
)

from gui.Ui_ALConfigWidget import Ui_ALConfigWidget
from gui.ALSeatMapWidget import ALSeatMapWidget
from gui.ALSeatMapTable import seats_maps
from gui.ALUserTreeWidget import TreeItemType
from gui.ALUserTreeWidget import ALUserTreeWidget

from utils.ConfigReader import ConfigReader
from utils.ConfigWriter import ConfigWriter


class ALConfigWidget(QWidget, Ui_ALConfigWidget):

    configWidgetCloseSingal = Signal(dict)

    def __init__(
        self,
        parent = None,
        config_paths = {
            "run": "",
            "user": ""
        }
    ):

        super().__init__(parent)

        self.setupUi(self)
        self.__config_paths = config_paths
        self.__config_data = {"run": {}, "user": {}}
        self.__seat_map_widget = None

        self.modifyUi()
        self.connectSignals()
        self.initlizeFloorRoomMap()
        self.initlizeDefaultConfigPaths()
        if not self.initlizeConfigs():
            self.close()


    def modifyUi(
        self
    ):

        self.setWindowFlags(Qt.WindowType.Window)
        # replace the treewidget with ALUserTreeWidget
        self.UserTreeWidget.setParent(None)
        self.UserTreeWidget.deleteLater()
        self.UserTreeWidget = ALUserTreeWidget()
        self.UserListLayout.insertWidget(0, self.UserTreeWidget)
        self.UserTreeWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.UserTreeWidget.customContextMenuRequested.connect(self.onUserTreeWidgetContextMenu)
        self.initlizeFloorRoomMap()
        self.initilizeUserInfoWidget()


    def connectSignals(
        self
    ):

        self.ShowPasswordCheckBox.clicked.connect(self.onShowPasswordCheckBoxChecked)
        self.FloorComboBox.currentIndexChanged.connect(self.onFloorComboBoxCurrentIndexChanged)
        self.SelectSeatsButton.clicked.connect(self.onSelectSeatsButtonClicked)
        self.UserTreeWidget.currentItemChanged.connect(self.onUserTreeWidgetCurrentItemChanged)
        self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)
        self.AddUserButton.clicked.connect(self.onAddUserButtonClicked)
        self.DelUserButton.clicked.connect(self.onDelUserButtonClicked)
        self.BrowseBrowserDriverButton.clicked.connect(self.onBrowseBrowserDriverButtonClicked)
        self.BrowseCurrentRunConfigButton.clicked.connect(self.onBrowseCurrentRunConfigButtonClicked)
        self.BrowseCurrentUserConfigButton.clicked.connect(self.onBrowseCurrentUserConfigButtonClicked)
        self.BrowseExportRunConfigButton.clicked.connect(self.onBrowseExportRunConfigButtonClicked)
        self.BrowseExportUserConfigButton.clicked.connect(self.onBrowseExportUserConfigButtonClicked)
        self.ExportConfigButton.clicked.connect(self.onExportConfigButtonClicked)
        self.NewConfigButton.clicked.connect(self.onNewConfigButtonClicked)
        self.LoadConfigButton.clicked.connect(self.onLoadConfigButtonClicked)
        self.ConfirmButton.clicked.connect(self.onConfirmButtonClicked)
        self.CancelButton.clicked.connect(self.onCancelButtonClicked)


    def showEvent(
        self,
        event
    ):

        result = super().showEvent(event)

        screen_rect = self.screen().geometry()
        target_pos = self.parent().geometry().center()
        target_pos.setX(target_pos.x() - self.width()//2)
        target_pos.setY(target_pos.y() - self.height()//2)
        if target_pos.x() < 0:
            target_pos.setX(0)
        if target_pos.x() + self.width() > screen_rect.width():
            target_pos.setX(screen_rect.width() - self.width())
        if target_pos.y() < 0:
            target_pos.setY(0)
        if target_pos.y() + self.height() > screen_rect.height():
            target_pos.setY(screen_rect.height() - self.height())
        self.move(target_pos)

        return result


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
    ):

        script_path = sys.executable
        script_dir = QFileInfo(script_path).absoluteDir()
        self.__default_config_paths = {
            "user": QDir.toNativeSeparators(script_dir.absoluteFilePath("user.json")),
            "run": QDir.toNativeSeparators(script_dir.absoluteFilePath("run.json"))
        }


    def initlizeConfigToWidget(
        self,
        which: str,
        config_data: dict
    ):

        if which == "run":
            self.setRunConfigToWidget(config_data)
            self.CurrentRunConfigEdit.setText(self.__config_paths["run"])
        elif which == "user":
            self.initilizeUserInfoWidget()
            self.fillUserTree(config_data)
            self.CurrentUserConfigEdit.setText(self.__config_paths["user"])


    def initlizeConfig(
        self,
        which: str
    ) -> bool:

        msg = ""
        is_success = True
        if which == "run":
            run_config_path = self.__config_paths[which]
            if not os.path.exists(run_config_path):
                self.__config_data[which] = self.defaultRunConfig()
                self.__config_paths[which] = self.__default_config_paths[which]
                if self.saveRunConfig(self.__config_paths[which], self.__config_data[which]):
                    msg += f"运行配置文件已初始化, 文件路径: \n{self.__config_paths[which]}\n"
                else:
                    is_success = False
            else:
                self.__config_data[which] = self.loadRunConfig(run_config_path)
                if self.__config_data[which] is None:
                    is_success = False
        elif which == "user":
            user_config_path = self.__config_paths[which]
            if not os.path.exists(user_config_path):
                self.__config_data[which] = self.defaultUserConfig()
                self.__config_paths[which] = self.__default_config_paths[which]
                if self.saveUserConfig(self.__config_paths[which], self.__config_data[which]):
                    msg += f"用户配置文件已初始化, 文件路径: \n{self.__config_paths[which]}\n"
                else:
                    is_success = False
            else:
                self.__config_data[which] = self.loadUserConfig(user_config_path)
                if self.__config_data[which] is None:
                    is_success = False
        if msg:
            QMessageBox.information(
                self,
                "提示 - AutoLibrary",
                f"配置文件初始化完成: \n{msg}"
            )
        return is_success


    def initlizeConfigs(
        self
    ) -> bool:

        is_success = True
        for which in ["run", "user"]:
            if not self.__config_paths[which]:
                self.__config_paths[which] = self.__default_config_paths[which]
            if not self.initlizeConfig(which):
                is_success = False
                break
            self.initlizeConfigToWidget(which, self.__config_data[which])
        return is_success


    def defaultRunConfig(
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


    def defaultUserConfig(
        self
    ) -> dict:

        return {
            "groups": []
        }


    def defaultGroup(
        self
    ) -> dict:

        return {
            "name": "默认分组",
            "enabled": True,
            "users": []
        }


    def defaultUsers(
        self
    ) -> dict:

        return {
            "users": []
        }


    def collectRunConfigFromWidget(
        self
    ) -> dict:

        run_config = self.defaultRunConfig()
        # library config is never changed
        run_config["login"]["auto_captcha"] = self.AutoCaptchaCheckBox.isChecked()
        run_config["login"]["max_attempt"] = self.LoginAttemptSpinBox.value()
        run_config["web_driver"]["driver_type"] = self.BrowserTypeComboBox.currentText()
        run_config["web_driver"]["driver_path"] = self.BrowseBrowserDriverEdit.text()
        run_config["web_driver"]["headless"] = self.HeadlessCheckBox.isChecked()
        run_mode = 0
        if self.AutoReserveCheckBox.isChecked():
            run_mode |= 0x01
        if self.AutoCheckinCheckBox.isChecked():
            run_mode |= 0x02
        if self.AutoRenewalCheckBox.isChecked():
            run_mode |= 0x04
        run_config["mode"]["run_mode"] = run_mode
        return run_config


    def setRunConfigToWidget(
        self,
        run_config: dict
    ):

        self.HostUrlEdit.setText(run_config["library"]["host_url"])
        self.LoginUrlEdit.setText(run_config["library"]["login_url"])
        self.AutoCaptchaCheckBox.setChecked(run_config["login"]["auto_captcha"])
        self.LoginAttemptSpinBox.setValue(run_config["login"]["max_attempt"])
        self.BrowserTypeComboBox.setCurrentText(run_config["web_driver"]["driver_type"])
        driver_path = os.path.abspath(run_config["web_driver"]["driver_path"])
        self.BrowseBrowserDriverEdit.setText(QDir.toNativeSeparators(driver_path))
        self.HeadlessCheckBox.setChecked(run_config["web_driver"]["headless"])
        run_mode = run_config["mode"]["run_mode"]
        self.AutoReserveCheckBox.setChecked(run_mode&0x01)
        self.AutoCheckinCheckBox.setChecked(run_mode&0x02)
        self.AutoRenewalCheckBox.setChecked(run_mode&0x04)


    def initilizeUserInfoWidget(
        self
    ):

        self.UsernameEdit.setText("")
        self.PasswordEdit.setText("")
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
        self.ExpectRenewDurationSpinBox.setValue(1.0)
        self.MaxRenewTimeDiffSpinBox.setValue(30)
        self.PreferLateRenewTimeCheckBox.setChecked(False)


    def collectUserFromUserInfoWidget(
        self
    ) -> dict:

        user = {
            "username": self.UsernameEdit.text(),
            "password": self.PasswordEdit.text(),
            "enabled": True,
            "reserve_info": {
                "begin_time":{},
                "end_time": {},
                "renew_time": {}
            }
        }
        user["reserve_info"]["date"] = self.DateEdit.dateTime().toString("yyyy-MM-dd")
        user["reserve_info"]["place"] = self.PlaceComboBox.currentText()
        user["reserve_info"]["floor"] = self.__floor_rmap[self.FloorComboBox.currentText()]
        user["reserve_info"]["room"] = self.__room_rmap[self.RoomComboBox.currentText()]
        user["reserve_info"]["seat_id"] = self.SeatIDEdit.text()
        user["reserve_info"]["begin_time"]["time"] = self.BeginTimeEdit.time().toString("HH:mm")
        user["reserve_info"]["begin_time"]["max_diff"] = self.MaxBeginTimeDiffSpinBox.value()
        user["reserve_info"]["begin_time"]["prefer_early"] = self.PreferEarlyBeginTimeCheckBox.isChecked()
        user["reserve_info"]["end_time"]["time"] = self.EndTimeEdit.time().toString("HH:mm")
        user["reserve_info"]["end_time"]["max_diff"] = self.MaxEndTimeDiffSpinBox.value()
        user["reserve_info"]["end_time"]["prefer_early"] = not self.PreferLateEndTimeCheckBox.isChecked()
        user["reserve_info"]["expect_duration"] = self.ExpectDurationSpinBox.value()
        user["reserve_info"]["satisfy_duration"] = self.SatisfyDurationCheckBox.isChecked()
        user["reserve_info"]["renew_time"]["expect_duration"] = self.ExpectRenewDurationSpinBox.value()
        user["reserve_info"]["renew_time"]["max_diff"] = self.MaxRenewTimeDiffSpinBox.value()
        user["reserve_info"]["renew_time"]["prefer_early"] = not self.PreferLateRenewTimeCheckBox.isChecked()
        return user


    def collectUserConfigFromUserTreeWidget(
        self
    ) -> dict:

        user_config = self.defaultUserConfig()
        for i in range(self.UserTreeWidget.topLevelItemCount()):
            group_item = self.UserTreeWidget.topLevelItem(i)
            group_config = {
                "name": group_item.text(0),
                "enabled": group_item.checkState(1) == Qt.CheckState.Checked,
                "users": []
            }
            for j in range(group_item.childCount()):
                user_item = group_item.child(j)
                user = user_item.data(0, Qt.UserRole)
                if not user:
                    continue
                user["enabled"] = user_item.checkState(1) == Qt.CheckState.Checked
                group_config["users"].append(user)
            user_config["groups"].append(group_config)
        return user_config


    def setUserToWidget(
        self,
        user: dict
    ) -> None:

        try:
            self.UsernameEdit.setText(user["username"])
            self.PasswordEdit.setText(user["password"])
            self.DateEdit.setDate(QDate.fromString(user["reserve_info"]["date"], "yyyy-MM-dd"))
            self.PlaceComboBox.setCurrentText(user["reserve_info"]["place"])
            self.FloorComboBox.setCurrentText(self.__floor_map[user["reserve_info"]["floor"]])
            self.RoomComboBox.setCurrentText(self.__room_map[user["reserve_info"]["room"]])
            self.SeatIDEdit.setText(user["reserve_info"]["seat_id"])
            self.BeginTimeEdit.setTime(QTime.fromString(user["reserve_info"]["begin_time"]["time"], "H:mm"))
            self.MaxBeginTimeDiffSpinBox.setValue(user["reserve_info"]["begin_time"]["max_diff"])
            self.PreferEarlyBeginTimeCheckBox.setChecked(user["reserve_info"]["begin_time"]["prefer_early"])
            self.EndTimeEdit.setTime(QTime.fromString(user["reserve_info"]["end_time"]["time"], "H:mm"))
            self.MaxEndTimeDiffSpinBox.setValue(user["reserve_info"]["end_time"]["max_diff"])
            self.PreferLateEndTimeCheckBox.setChecked(not user["reserve_info"]["end_time"]["prefer_early"])
            self.ExpectDurationSpinBox.setValue(user["reserve_info"]["expect_duration"])
            self.SatisfyDurationCheckBox.setChecked(user["reserve_info"]["satisfy_duration"])
            self.ExpectRenewDurationSpinBox.setValue(user["reserve_info"]["renew_time"]["expect_duration"])
            self.MaxRenewTimeDiffSpinBox.setValue(user["reserve_info"]["renew_time"]["max_diff"])
            self.PreferLateRenewTimeCheckBox.setChecked(not user["reserve_info"]["renew_time"]["prefer_early"])
        except:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                "用户配置文件读取发生错误 !\n"\
                f"用户: {user['username']} 配置文件可能已损坏"
            )


    def loadRunConfig(
        self,
        run_config_path: str
    ) -> dict:

        try:
            if not run_config_path or not os.path.exists(run_config_path):
                raise Exception("文件路径不存在")
            run_config = ConfigReader(run_config_path).getConfigs()
            if run_config and "library" in run_config\
                and "web_driver" in run_config\
                and "login" in run_config:
                return run_config
            return None
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"运行配置文件读取发生错误 ! : {e}\n"\
                f"文件路径: {run_config_path}"
            )
            return None


    def saveRunConfig(
        self,
        run_config_path: str,
        run_config_data: dict
    ) -> bool:

        try:
            if not run_config_path:
                raise Exception("文件路径为空")
            if not run_config_data or not isinstance(run_config_data, dict):
                raise Exception("运行配置数据为空或类型错误")
            ConfigWriter(run_config_path, run_config_data)
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"配置文件写入发生错误 ! : {e}\n"\
                f"文件路径: {run_config_path}"
            )
            return False


    def loadUserConfig(
        self,
        user_config_path: str
    ) -> dict:

        try:
            if not user_config_path or not os.path.exists(user_config_path):
                raise Exception("文件路径不存在")
            user_config = ConfigReader(user_config_path).getConfigs()
            if user_config and "groups" in user_config:
                return user_config
            # compatibility with old version config format
            if user_config and "users" in user_config:
                user_config = {
                    "groups": [
                        {
                            "name": f"兼容分组-{QFileInfo(user_config_path).fileName()}",
                            "enabled": True,
                            "users": user_config["users"]
                        }
                    ]
                }
                return user_config
            return None
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取发生错误 ! : {e}\n"\
                f"文件路径: {user_config_path}"
            )
            return None


    def saveUserConfig(
        self,
        user_config_path: str,
        user_config_data: dict
    ) -> bool:

        try:
            if not user_config_path:
                raise Exception("文件路径为空")
            if not user_config_data or not isinstance(user_config_data, dict):
                raise Exception("用户配置数据为空或类型错误")
            ConfigWriter(user_config_path, user_config_data)
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件写入发生错误 ! : {e}\n"\
                f"文件路径: \n{user_config_path}"
            )
            return False


    def saveConfigs(
        self,
        run_config_path: str,
        user_config_path: str
    ) -> bool:

        if user_config_path:
            self.__config_data["user"] = self.collectUserConfigFromUserTreeWidget()
            if not self.saveUserConfig(
                user_config_path,
                self.__config_data["user"]
            ):
                return False
        if run_config_path:
            self.__config_data["run"] = self.collectRunConfigFromWidget()
            if not self.saveRunConfig(
                run_config_path,
                self.__config_data["run"]
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
            run_config = self.loadRunConfig(config_path)
            user_config = self.loadUserConfig(config_path)
            if run_config is not None:
                self.__config_data["run"].update(run_config)
                self.setRunConfigToWidget(self.__config_data["run"])
                return True
            if user_config is not None:
                self.__config_data["user"].update(user_config)
                self.fillUserTree(self.__config_data["user"])
                return True
        except:
            return False


    def fillUserTree(
        self,
        user_config_data: dict
    ):

        self.UserTreeWidget.clear()
        self.UserTreeWidget.itemChanged.disconnect(self.onUserTreeWidgetItemChanged)
        try:
            if "groups" in user_config_data:
                for group_config in user_config_data["groups"]:
                    group_item = QTreeWidgetItem(self.UserTreeWidget, TreeItemType.GROUP.value)
                    group_item.setText(0, group_config["name"])
                    group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
                    group_item.setCheckState(1, Qt.Checked if group_config.get("enabled", True) else Qt.Unchecked)
                    for user_config in group_config["users"]:
                        user_item = QTreeWidgetItem(group_item, TreeItemType.USER.value)
                        user_item.setText(0, user_config["username"])
                        user_item.setText(1, "" if user_config.get("enabled", True) else "跳过")
                        user_item.setData(0, Qt.UserRole, user_config)
                        user_item.setCheckState(1, Qt.Checked if user_config.get("enabled", True) else Qt.Unchecked)
                        user_item.setDisabled(not group_config.get("enabled", True))
                    group_item.setExpanded(True)
        finally:
            self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)


    def addGroup(
        self,
        group_name: str = ""
    ) -> QTreeWidgetItem:

        self.UserTreeWidget.itemChanged.disconnect(self.onUserTreeWidgetItemChanged)
        group_item = QTreeWidgetItem(self.UserTreeWidget, TreeItemType.GROUP.value)
        if not group_name:
            group_name = f"新分组-{self.UserTreeWidget.topLevelItemCount()}"
        group_item.setText(0, group_name)
        group_item.setFlags(group_item.flags() | Qt.ItemIsEditable)
        group_item.setCheckState(1, Qt.Checked)
        self.UserTreeWidget.setCurrentItem(group_item)
        self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)
        return group_item


    def addUser(
        self,
        group_item: QTreeWidgetItem = None
    ) -> QTreeWidgetItem:

        if group_item is None:
            current_item = self.UserTreeWidget.currentItem()
            if current_item is None:
                group_item = self.addGroup()
        if group_item.type() == TreeItemType.USER.value:
            group_item = group_item.parent()
        if group_item.checkState(1) == Qt.CheckState.Unchecked:
            return None
        new_user = {
            "username": f"新用户-{group_item.childCount()}",
            "password": "000000",
            "enabled": True,
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
                "satisfy_duration": False,
                "renew_time": {
                    "expect_duration": 1.0,
                    "max_diff": 30,
                    "prefer_early": True
                }
            }
        }
        self.UserTreeWidget.itemChanged.disconnect(self.onUserTreeWidgetItemChanged)
        user_item = QTreeWidgetItem(group_item, TreeItemType.USER.value)
        user_item.setText(0, new_user["username"])
        user_item.setText(1, "")
        user_item.setData(0, Qt.UserRole, new_user)
        user_item.setCheckState(1, Qt.CheckState.Checked)
        group_item.setExpanded(True)
        self.UserTreeWidget.setCurrentItem(user_item)
        self.setUserToWidget(new_user)
        self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)
        return user_item


    def delUser(
        self,
        user_item: QTreeWidgetItem = None
    ):

        if user_item is None:
            return
        if user_item.type() != TreeItemType.USER.value:
            return
        parent_item = user_item.parent()
        index = parent_item.indexOfChild(user_item)
        parent_item.takeChild(index)
        if parent_item.childCount() == 0:
            self.UserTreeWidget.setCurrentItem(None)


    def delGroup(
        self,
        group_item: QTreeWidgetItem = None
    ):

        if group_item is None:
            return
        if group_item.type() != TreeItemType.GROUP.value:
            return
        index = self.UserTreeWidget.indexOfTopLevelItem(group_item)
        self.UserTreeWidget.takeTopLevelItem(index)


    def renameItem(
        self,
        item: QTreeWidgetItem,
    ):

        if item is None:
            return
        old_name = item.text(0)
        if item.parent() is None:
            item_type = "分组"
        else:
            item_type = "用户"
        new_name, ok = QInputDialog.getText(
            self, f"重命名{item_type}项 : '{old_name}'", f"请输入新的{item_type}名:", text=old_name
        )
        new_name = new_name.strip()
        if not ok or not new_name:
            return
        item.setText(0, new_name)
        if item.type() == TreeItemType.GROUP.value:
            item.setText(0, new_name)
        else:
            user = item.data(0, Qt.UserRole)
            user["username"] = new_name
            item.setText(0, new_name)
            item.setData(0, Qt.UserRole, user)
            self.setUserToWidget(user)


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
    def onSeatMapWidgetClosed(
        self,
        selected_seats: list[str]
    ):

        self.__seat_map_widget.seatMapWidgetClosed.disconnect(self.onSeatMapWidgetClosed)
        self.__seat_map_widget.deleteLater()
        self.__seat_map_widget = None
        if len(selected_seats) == 0:
            return
        self.SeatIDEdit.setText(",".join(selected_seats))

    @Slot()
    def onSelectSeatsButtonClicked(
        self
    ):

        floor = self.FloorComboBox.currentText()
        room = self.RoomComboBox.currentText()
        floor_idx = self.__floor_rmap[floor]
        room_idx = self.__room_rmap[room]
        if self.__seat_map_widget is None:
            self.__seat_map_widget = ALSeatMapWidget(
                self,
                floor,
                room,
                seats_maps[floor_idx][room_idx]
            )
            self.__seat_map_widget.seatMapWidgetClosed.connect(self.onSeatMapWidgetClosed)
        self.__seat_map_widget.show()
        self.__seat_map_widget.raise_()
        self.__seat_map_widget.activateWindow()
        self.__seat_map_widget.selectSeats(self.SeatIDEdit.text().split(","))

    @Slot()
    def onUserTreeWidgetCurrentItemChanged(
        self,
        current: QTreeWidgetItem,
        previous: QTreeWidgetItem
    ):
        # dont care about the 'self.__config_data["user"]', we already
        # cant effectively update the data of each user, due to the
        # possiblity of frequency edit. we just let the QListWidget
        # help us.
        if previous and previous.type() == TreeItemType.USER.value:
            user = self.collectUserFromUserInfoWidget()
            if user:
                self.UsernameEdit.textEdited.disconnect()
                user["enabled"] = previous.checkState(1) == Qt.Checked
                previous.setText(0, user["username"])
                previous.setText(1, "" if user.get("enabled", True) else "跳过")
                previous.setData(0, Qt.UserRole, user)
        if current is None:
            self.initilizeUserInfoWidget()
            return
        if current.type() == TreeItemType.USER.value:
            user = current.data(0, Qt.UserRole)
            if user:
                self.setUserToWidget(user)
                self.UsernameEdit.textEdited.connect(lambda text: current.setText(0, text))
        else:
            self.initilizeUserInfoWidget()

    @Slot()
    def onUserTreeWidgetItemChanged(
        self,
        item: QTreeWidgetItem,
        column: int
    ):

        if item is None:
            return
        if column != 1:
            return
        if item.type() == TreeItemType.GROUP.value:
            is_checked = item.checkState(1) == Qt.CheckState.Checked
            for i in range(item.childCount()):
                child = item.child(i)
                if self.UserTreeWidget.currentItem() == child:
                    self.UserTreeWidget.setCurrentItem(item)
                child.setDisabled(not is_checked)
        else:
            is_checked = item.checkState(1) == Qt.CheckState.Checked
            item.setText(1, "" if is_checked else "跳过")


    def showTreeMenu(
        self,
        menu: QMenu
    ):

        add_group_action = QAction("添加分组", menu)
        add_group_action.triggered.connect(self.addGroup)
        menu.addAction(add_group_action)


    def showGroupMenu(
        self,
        menu: QMenu,
        group_item: QTreeWidgetItem = None
    ):

        add_user_action = QAction("添加用户", menu)
        rename_group_action = QAction("重命名分组", menu)
        del_group_action = QAction("删除分组", menu)
        add_user_action.triggered.connect(lambda: self.addUser(group_item))
        rename_group_action.triggered.connect(lambda: self.renameItem(group_item))
        del_group_action.triggered.connect(lambda: self.delGroup(group_item))
        menu.addAction(add_user_action)
        menu.addSeparator()
        menu.addAction(rename_group_action)
        menu.addAction(del_group_action)
        if group_item.checkState(1) == Qt.CheckState.Unchecked:
            add_user_action.setEnabled(False)


    def showUserMenu(
        self,
        menu: QMenu,
        user_item: QTreeWidgetItem = None
    ):

        rename_user_action = QAction("重命名用户", menu)
        del_user_action = QAction("删除用户", menu)
        rename_user_action.triggered.connect(lambda: self.renameItem(user_item))
        del_user_action.triggered.connect(lambda: self.delUser(user_item))
        menu.addAction(rename_user_action)
        menu.addAction(del_user_action)

    @Slot()
    def onUserTreeWidgetContextMenu(
        self,
        pos
    ):

        current_item = self.UserTreeWidget.itemAt(pos)
        menu = QMenu(self.UserTreeWidget)
        if current_item is None:
            self.showTreeMenu(menu)
        elif current_item.type() == TreeItemType.GROUP.value:
            self.showGroupMenu(menu, current_item)
        else:
            self.showUserMenu(menu, current_item)
        menu.exec_(self.UserTreeWidget.mapToGlobal(pos))

    @Slot()
    def onAddUserButtonClicked(
        self
    ):

        current_item = self.UserTreeWidget.currentItem()
        self.addUser(current_item)

    @Slot()
    def onDelUserButtonClicked(
        self
    ):

        current_item = self.UserTreeWidget.currentItem()
        self.delUser(current_item)

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
    def onBrowseCurrentRunConfigButtonClicked(
        self
    ):

        run_config_path = QFileDialog.getOpenFileName(
            self,
            "选择其它的运行配置 - AutoLibrary",
            self.CurrentRunConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if run_config_path:
            run_config_path = QDir.toNativeSeparators(run_config_path)
            if self.loadConfig(run_config_path):
                self.__config_paths["run"] = run_config_path
                self.CurrentRunConfigEdit.setText(run_config_path)

    @Slot()
    def onBrowseCurrentUserConfigButtonClicked(
        self
    ):

        user_config_path = QFileDialog.getOpenFileName(
            self,
            "选择其它的用户配置 - AutoLibrary",
            self.CurrentUserConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if user_config_path:
            user_config_path = QDir.toNativeSeparators(user_config_path)
            if self.loadConfig(user_config_path):
                self.__config_paths["user"] = user_config_path
                self.CurrentUserConfigEdit.setText(user_config_path)

    @Slot()
    def onBrowseExportRunConfigButtonClicked(
        self
    ):

        run_config_path = QFileDialog.getSaveFileName(
            self,
            "导出运行配置 - AutoLibrary",
            self.CurrentRunConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if run_config_path:
            self.ExportRunConfigEdit.setText(QDir.toNativeSeparators(run_config_path))

    @Slot()
    def onBrowseExportUserConfigButtonClicked(
        self
    ):

        user_config_path = QFileDialog.getSaveFileName(
            self,
            "导出用户配置 - AutoLibrary",
            self.CurrentUserConfigEdit.text(),
            "JSON 文件 (*.json);;所有文件 (*)"
        )[0]
        if user_config_path:
            self.ExportUserConfigEdit.setText(QDir.toNativeSeparators(user_config_path))

    @Slot()
    def onExportConfigButtonClicked(
        self
    ):

        msg = ""

        run_config_path = self.ExportRunConfigEdit.text()
        user_config_path = self.ExportUserConfigEdit.text()
        if run_config_path:
            if self.saveConfigs(
                run_config_path, ""
            ):
                msg += f"运行配置文件已导出到: \n'{run_config_path}'\n"
            else:
                msg += f"运行配置文件导出失败: \n'{run_config_path}'\n"
        if user_config_path:
            if self.saveConfigs(
                "", user_config_path
            ):
                msg += f"用户配置文件已导出到: \n'{user_config_path}'\n"
            else:
                msg += f"用户配置文件导出失败: \n'{user_config_path}'\n"
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

        file_path = self.CurrentRunConfigEdit.text()
        folder_dir = QFileDialog.getExistingDirectory(
            self,
            "选择新建配置的文件夹 - AutoLibrary",
            QDir.toNativeSeparators(QFileInfo(os.path.abspath(file_path)).absoluteDir().path())
        )
        if not folder_dir:
            return
        run_config_path = QDir.toNativeSeparators(os.path.join(folder_dir, "run.json"))
        user_config_path = QDir.toNativeSeparators(os.path.join(folder_dir, "user.json"))
        run_exists = os.path.isfile(run_config_path)
        user_exists = os.path.isfile(user_config_path)
        if run_exists or user_exists:
            exist_files = []
            if run_exists:
                exist_files.append(run_config_path)
            if user_exists:
                exist_files.append(user_config_path)
            reply = QMessageBox.information(
                self,
                "提示 - AutoLibrary",
                f"文件夹中已存在以下文件, 是否覆盖 ?\n{chr(10).join(exist_files)}",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.__config_data["run"] = self.defaultRunConfig()
        self.__config_data["user"] = self.defaultUserConfig()
        self.__config_paths = {
            "run": run_config_path,
            "user": user_config_path
        }
        self.initlizeConfigToWidget("run", self.__config_data["run"])
        self.initlizeConfigToWidget("user", self.__config_data["user"])

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        current_item = self.UserTreeWidget.currentItem()
        if current_item and current_item.type() == TreeItemType.USER.value:
            self.UserTreeWidget.setCurrentItem(None)
        if self.saveConfigs(
            self.__config_paths["run"],
            self.__config_paths["user"]
        ):
            QMessageBox.information(
                self,
                "提示 - AutoLibrary",
                "配置文件保存成功 !\n"
                f"运行配置文件路径: \n{self.__config_paths['run']}\n"\
                f"用户配置文件路径: \n{self.__config_paths['user']}"
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