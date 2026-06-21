# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import os

from PySide6.QtCore import (
    QDate,
    QDir,
    QFileInfo,
    Qt,
    QTime,
    Signal,
    Slot
)
from PySide6.QtGui import (
    QAction,
    QCloseEvent
)
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QMenu,
    QMessageBox,
    QTreeWidgetItem,
    QWidget
)

import managers.config.ConfigManager as ConfigManager

from gui.ALSeatMapSelectDialog import ALSeatMapSelectDialog
from gui.ALSeatMapTable import ALSeatMapTable
from gui.ALUserTreeWidget import (
    ALUserTreeItemType,
    ALUserTreeWidget
)
from gui.ALWebDriverDownloadDialog import ALWebDriverDownloadDialog
from gui.ALWidgetMixin import CenterOnParentMixin
from gui.resources.ui.Ui_ALConfigWidget import Ui_ALConfigWidget
from interfaces.ConfigProvider import (
    CfgKey,
    ConfigProvider
)
from managers.config.ConfigUtils import ConfigUtils
from utils.JSONReader import JSONReader
from utils.JSONWriter import JSONWriter


class ALConfigWidget(CenterOnParentMixin, QWidget, Ui_ALConfigWidget):

    configWidgetIsClosed = Signal()

    def __init__(
        self,
        parent = None,
    ):

        super().__init__(parent)
        self.__cfg_mgr: ConfigProvider = ConfigManager.instance()
        self.__config_paths = ConfigUtils.getAutomationConfigPaths()
        self.__config_data = {"run": {}, "user": {}}

        self.setupUi(self)
        self.modifyUi()
        self.connectSignals()
        if not self.initializeConfigs():
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
        self.initializeFloorRoomMap()
        self.initializeUserInfoWidget()

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
        self.AutoDownloadWebDriverButton.clicked.connect(self.onAutoDownloadWebDriverButtonClicked)
        self.BrowseCurrentRunConfigButton.clicked.connect(self.onBrowseCurrentRunConfigButtonClicked)
        self.BrowseCurrentUserConfigButton.clicked.connect(self.onBrowseCurrentUserConfigButtonClicked)
        self.BrowseExportRunConfigButton.clicked.connect(self.onBrowseExportRunConfigButtonClicked)
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

        self.configWidgetIsClosed.emit()
        super().closeEvent(event)

    def initializeFloorRoomMap(
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
            "2": "二层西区",
            "3": "三层内环",
            "4": "三层外环",
            "5": "四层内环",
            "6": "四层外环",
            "7": "四层期刊",
            "8": "五层考研"
        }
        self.__floor_rmap = {
            v: k for k, v in self.__floor_map.items()
        }
        self.__room_rmap = {
            v: k for k, v in self.__room_map.items()
        }
        self.__floor_room_map = {
            "二层": ["二层内环", "二层西区"],
            "三层": ["三层内环", "三层外环"],
            "四层": ["四层内环", "四层外环", "四层期刊"],
            "五层": ["五层考研"]
        }

    def initializeConfigToWidget(
        self,
        which: str,
        config_data: dict
    ):

        if which == "run":
            self.setRunConfigToWidget(config_data)
            self.CurrentRunConfigEdit.setText(self.__config_paths["run"])
        elif which == "user":
            self.initializeUserInfoWidget()
            self.setUsersToTreeWidget(config_data)
            self.CurrentUserConfigEdit.setText(self.__config_paths["user"])

    def initializeConfig(
        self,
        which: str
    ) -> bool:

        msg = "" # no use for now
        is_success = True
        if which == "run":
            run_config_path = self.__config_paths[which]
            if not os.path.exists(run_config_path):
                self.__config_data[which] = self.defaultRunConfig()
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
                if self.saveUserConfig(self.__config_paths[which], self.__config_data[which]):
                    msg += f"用户配置文件已初始化, 文件路径: \n{self.__config_paths[which]}\n"
                else:
                    is_success = False
            else:
                self.__config_data[which] = self.loadUserConfig(user_config_path)
                if self.__config_data[which] is None:
                    is_success = False
        return is_success

    def initializeConfigs(
        self
    ) -> bool:

        is_success = True
        for which in ["run", "user"]:
            if not self.initializeConfig(which):
                is_success = False
                break
            self.initializeConfigToWidget(which, self.__config_data[which])
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
                "driver_path": "",
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
            "groups": [
            ]
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

        try:
            self.HostUrlEdit.setText(run_config["library"]["host_url"])
            self.LoginUrlEdit.setText(run_config["library"]["login_url"])
            self.AutoCaptchaCheckBox.setChecked(run_config["login"]["auto_captcha"])
            self.LoginAttemptSpinBox.setValue(run_config["login"]["max_attempt"])
            self.BrowserTypeComboBox.setCurrentText(run_config["web_driver"]["driver_type"])
            if run_config["web_driver"]["driver_path"]:
                driver_path = os.path.abspath(run_config["web_driver"]["driver_path"])
            else:
                driver_path = ""
            self.BrowseBrowserDriverEdit.setText(QDir.toNativeSeparators(driver_path))
            self.HeadlessCheckBox.setChecked(run_config["web_driver"]["headless"])
            run_mode = run_config["mode"]["run_mode"]
            self.AutoReserveCheckBox.setChecked(run_mode&0x01)
            self.AutoCheckinCheckBox.setChecked(run_mode&0x02)
            self.AutoRenewalCheckBox.setChecked(run_mode&0x04)
        except KeyError as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"运行配置文件读取键 '{e}' 时发生错误 ! :\n"
                f"文件路径: {self.__config_paths['run']}\n"
                "文件可能被意外修改或已经损坏\n"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"运行配置文件读取键 '{e}' 时发生未知错误 ! :\n"
                f"文件路径: {self.__config_paths['run']}\n"
                "文件可能被意外修改或已经损坏\n"
            )

    def initializeUserInfoWidget(
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

    def collectUserFromWidget(
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

    def collectUsersFromTreeWidget(
        self
    ) -> dict:

        user_config = self.defaultUserConfig()
        for i in range(self.UserTreeWidget.topLevelItemCount()):
            GroupItem = self.UserTreeWidget.topLevelItem(i)
            group_config = {
                "name": GroupItem.text(0),
                "enabled": GroupItem.checkState(1) == Qt.CheckState.Checked,
                "users": []
            }
            for j in range(GroupItem.childCount()):
                UserItem = GroupItem.child(j)
                user = UserItem.data(0, Qt.UserRole)
                if not user:
                    continue
                user["enabled"] = UserItem.checkState(1) == Qt.CheckState.Checked
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
        except KeyError as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取键 '{e}' 时发生错误 ! :\n"
                f"文件路径: {self.__config_paths['user']}\n"
                "文件可能被意外修改或已经损坏\n"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取键 '{e}' 时发生未知错误 ! :\n"
                f"文件路径: {self.__config_paths['user']}\n"
                "文件可能被意外修改或已经损坏\n"
            )

    def setUsersToTreeWidget(
        self,
        users: dict
    ):

        self.UserTreeWidget.clear()
        self.UserTreeWidget.itemChanged.disconnect(self.onUserTreeWidgetItemChanged)
        try:
            if "groups" in users:
                for group_config in users["groups"]:
                    GroupItem = QTreeWidgetItem(self.UserTreeWidget, ALUserTreeItemType.GROUP.value)
                    GroupItem.setText(0, group_config["name"])
                    GroupItem.setFlags(GroupItem.flags() | Qt.ItemIsEditable)
                    GroupItem.setCheckState(1, Qt.Checked if group_config.get("enabled", True) else Qt.Unchecked)
                    for user_config in group_config["users"]:
                        UserItem = QTreeWidgetItem(GroupItem, ALUserTreeItemType.USER.value)
                        UserItem.setText(0, user_config["username"])
                        UserItem.setText(1, "" if user_config.get("enabled", True) else "跳过")
                        UserItem.setData(0, Qt.UserRole, user_config)
                        UserItem.setCheckState(1, Qt.Checked if user_config.get("enabled", True) else Qt.Unchecked)
                        UserItem.setDisabled(not group_config.get("enabled", True))
                    GroupItem.setExpanded(True)
        except KeyError as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取键 '{e}' 时发生错误 ! :\n"
                f"文件路径: {self.__config_paths['user']}\n"
                "文件可能被意外修改或已经损坏\n"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取键 '{e}' 时发生未知错误 ! :\n"
                f"文件路径: {self.__config_paths['user']}\n"
                "文件可能被意外修改或已经损坏\n"
            )
        finally:
            self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)

    def loadRunConfig(
        self,
        run_config_path: str
    ) -> dict:

        try:
            if not run_config_path or not os.path.exists(run_config_path):
                raise Exception("文件路径不存在")
            run_config = JSONReader(run_config_path).data()
            if run_config and "library" in run_config\
                and "web_driver" in run_config\
                and "login" in run_config:
                return run_config
            else:
                return None
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"运行配置文件读取发生错误 ! :\n{e}"
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
            JSONWriter(run_config_path, run_config_data)
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"配置文件写入发生错误 ! : \n{e}"
            )
            return False

    def loadUserConfig(
        self,
        user_config_path: str
    ) -> dict:

        try:
            if not user_config_path or not os.path.exists(user_config_path):
                raise Exception("文件路径不存在")
            user_config = JSONReader(user_config_path).data()
            if user_config and "groups" in user_config:
                return user_config
            # compatibility with old version config format
            elif user_config and "users" in user_config:
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
            else:
                return None
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件读取发生错误 ! :\n{e}"
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
            JSONWriter(user_config_path, user_config_data)
            return True
        except Exception as e:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                f"用户配置文件写入发生错误 ! :\n{e}"
            )
            return False

    def saveConfigs(
        self,
        run_config_path: str,
        user_config_path: str
    ) -> bool:

        if user_config_path:
            self.__config_data["user"] = self.collectUsersFromTreeWidget()
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
                self.setUsersToTreeWidget(self.__config_data["user"])
                return True
        except:
            return False

    def addGroup(
        self,
        group_name: str = ""
    ) -> QTreeWidgetItem:

        self.UserTreeWidget.itemChanged.disconnect(self.onUserTreeWidgetItemChanged)
        GroupItem = QTreeWidgetItem(self.UserTreeWidget, ALUserTreeItemType.GROUP.value)
        if not group_name:
            group_name = f"新分组-{self.UserTreeWidget.topLevelItemCount()}"
        GroupItem.setText(0, group_name)
        GroupItem.setFlags(GroupItem.flags() | Qt.ItemIsEditable)
        GroupItem.setCheckState(1, Qt.Checked)
        self.UserTreeWidget.setCurrentItem(GroupItem)
        self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)
        return GroupItem

    def delGroup(
        self,
        GroupItem: QTreeWidgetItem = None
    ):

        if GroupItem is None:
            return
        if GroupItem.type() != ALUserTreeItemType.GROUP.value:
            return
        index = self.UserTreeWidget.indexOfTopLevelItem(GroupItem)
        self.UserTreeWidget.takeTopLevelItem(index)

    def addUser(
        self,
        GroupItem: QTreeWidgetItem = None
    ) -> QTreeWidgetItem:

        if GroupItem is None:
            CurrentItem = self.UserTreeWidget.currentItem()
            if CurrentItem is None:
                GroupItem = self.addGroup()
        if GroupItem.type() == ALUserTreeItemType.USER.value:
            GroupItem = GroupItem.parent()
        if GroupItem.checkState(1) == Qt.CheckState.Unchecked:
            return None
        new_user = {
            "username": f"新用户-{GroupItem.childCount()}",
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
        UserItem = QTreeWidgetItem(GroupItem, ALUserTreeItemType.USER.value)
        UserItem.setText(0, new_user["username"])
        UserItem.setText(1, "")
        UserItem.setData(0, Qt.UserRole, new_user)
        UserItem.setCheckState(1, Qt.CheckState.Checked)
        GroupItem.setExpanded(True)
        self.UserTreeWidget.setCurrentItem(UserItem)
        self.setUserToWidget(new_user)
        self.UserTreeWidget.itemChanged.connect(self.onUserTreeWidgetItemChanged)
        return UserItem

    def delUser(
        self,
        UserItem: QTreeWidgetItem = None
    ):

        if UserItem is None:
            return
        if UserItem.type() != ALUserTreeItemType.USER.value:
            return
        ParentItem = UserItem.parent()
        index = ParentItem.indexOfChild(UserItem)
        ParentItem.takeChild(index)
        if ParentItem.childCount() == 0:
            self.UserTreeWidget.setCurrentItem(None)

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
        if item.type() == ALUserTreeItemType.GROUP.value:
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
    def onSelectSeatsButtonClicked(
        self
    ):

        floor = self.FloorComboBox.currentText()
        room = self.RoomComboBox.currentText()
        floor_idx = self.__floor_rmap[floor]
        room_idx = self.__room_rmap[room]
        Dialog = ALSeatMapSelectDialog(
            self,
            floor,
            room,
            ALSeatMapTable[floor_idx][room_idx]
        )
        Dialog.selectSeats(self.SeatIDEdit.text().split(","))
        if Dialog.exec() == QDialog.DialogCode.Accepted:
            selected_seats = Dialog.getSelectedSeats()
            if len(selected_seats) == 0:
                self.SeatIDEdit.clear()
                return
            self.SeatIDEdit.setText(",".join(Dialog.getSelectedSeats()))

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
        if previous and previous.type() == ALUserTreeItemType.USER.value:
            user = self.collectUserFromWidget()
            if user:
                self.UsernameEdit.textEdited.disconnect()
                user["enabled"] = previous.checkState(1) == Qt.Checked
                previous.setText(0, user["username"])
                previous.setText(1, "" if user.get("enabled", True) else "跳过")
                previous.setData(0, Qt.UserRole, user)
        if current is None:
            self.initializeUserInfoWidget()
            return
        if current.type() == ALUserTreeItemType.USER.value:
            user = current.data(0, Qt.UserRole)
            if user:
                self.setUserToWidget(user)
                self.UsernameEdit.textEdited.connect(lambda text: current.setText(0, text))
        else:
            self.initializeUserInfoWidget()

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
        if item.type() == ALUserTreeItemType.GROUP.value:
            is_checked = item.checkState(1) == Qt.CheckState.Checked
            for i in range(item.childCount()):
                Child = item.child(i)
                if self.UserTreeWidget.currentItem() == Child:
                    self.UserTreeWidget.setCurrentItem(item)
                Child.setDisabled(not is_checked)
        else:
            is_checked = item.checkState(1) == Qt.CheckState.Checked
            item.setText(1, "" if is_checked else "跳过")

    def showTreeMenu(
        self,
        menu: QMenu
    ):

        AddGroupAction = QAction("添加分组", menu)
        AddGroupAction.triggered.connect(self.addGroup)
        menu.addAction(AddGroupAction)

    def showGroupMenu(
        self,
        menu: QMenu,
        GroupItem: QTreeWidgetItem = None
    ):

        AddUserAction = QAction("添加用户", menu)
        RenameGroupAction = QAction("重命名分组", menu)
        DelGroupAction = QAction("删除分组", menu)
        AddUserAction.triggered.connect(lambda: self.addUser(GroupItem))
        RenameGroupAction.triggered.connect(lambda: self.renameItem(GroupItem))
        DelGroupAction.triggered.connect(lambda: self.delGroup(GroupItem))
        menu.addAction(AddUserAction)
        menu.addSeparator()
        menu.addAction(RenameGroupAction)
        menu.addAction(DelGroupAction)
        if GroupItem.checkState(1) == Qt.CheckState.Unchecked:
            AddUserAction.setEnabled(False)

    def showUserMenu(
        self,
        menu: QMenu,
        UserItem: QTreeWidgetItem = None
    ):

        RenameUserAction = QAction("重命名用户", menu)
        DelUserAction = QAction("删除用户", menu)
        RenameUserAction.triggered.connect(lambda: self.renameItem(UserItem))
        DelUserAction.triggered.connect(lambda: self.delUser(UserItem))
        menu.addAction(RenameUserAction)
        menu.addAction(DelUserAction)

    @Slot()
    def onUserTreeWidgetContextMenu(
        self,
        pos
    ):

        CurrentItem = self.UserTreeWidget.itemAt(pos)
        Menu = QMenu(self.UserTreeWidget)
        if CurrentItem is None:
            self.showTreeMenu(Menu)
        elif CurrentItem.type() == ALUserTreeItemType.GROUP.value:
            self.showGroupMenu(Menu, CurrentItem)
        else:
            self.showUserMenu(Menu, CurrentItem)
        Menu.exec_(self.UserTreeWidget.mapToGlobal(pos))

    @Slot()
    def onAddUserButtonClicked(
        self
    ):

        CurrentItem = self.UserTreeWidget.currentItem()
        self.addUser(CurrentItem)

    @Slot()
    def onDelUserButtonClicked(
        self
    ):

        CurrentItem = self.UserTreeWidget.currentItem()
        self.delUser(CurrentItem)

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
    def onAutoDownloadWebDriverButtonClicked(
        self
    ):

        Dialog = ALWebDriverDownloadDialog(self)
        Dialog.show()
        Dialog.exec_()
        selected_driver_info = Dialog.getSelectedDriverInfo()
        if selected_driver_info and selected_driver_info.driver_path:
            self.BrowserTypeComboBox.setCurrentText(selected_driver_info.driver_type.value)
            self.BrowseBrowserDriverEdit.setText(QDir.toNativeSeparators(str(selected_driver_info.driver_path)))

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
            data = self.loadRunConfig(run_config_path)
            if data is not None:
                self.__config_data["run"].update(data)
                self.setRunConfigToWidget(data)
                self.__config_paths["run"] = run_config_path
                self.CurrentRunConfigEdit.setText(run_config_path)
                paths = self.__cfg_mgr.get(CfgKey.GLOBAL.AUTOMATION.RUN_PATH.PATHS, [])
                if run_config_path not in paths:
                    paths.append(run_config_path)
                    index = len(paths) - 1
                else:
                    index = paths.index(run_config_path)
                self.__cfg_mgr.set(CfgKey.GLOBAL.AUTOMATION.RUN_PATH.ROOT, {"current": index, "paths": paths})
            else:
                QMessageBox.warning(
                    self,
                    "警告 - AutoLibrary",
                    "运行配置文件读取发生错误 ! :\n"\
                    "无法从选择的运行配置文件中加载数据 ! :\n"\
                    "可能选择了错误的配置文件类型"
                )

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
            data = self.loadUserConfig(user_config_path)
            if data is not None:
                self.__config_data["user"].update(data)
                self.setUsersToTreeWidget(data)
                self.__config_paths["user"] = user_config_path
                self.CurrentUserConfigEdit.setText(user_config_path)
                paths = self.__cfg_mgr.get(CfgKey.GLOBAL.AUTOMATION.USER_PATH.PATHS, [])
                if user_config_path not in paths:
                    paths.append(user_config_path)
                    index = len(paths) - 1
                else:
                    index = paths.index(user_config_path)
                self.__cfg_mgr.set(CfgKey.GLOBAL.AUTOMATION.USER_PATH.ROOT, {"current": index, "paths": paths})
            else:
                QMessageBox.warning(
                    self,
                    "警告 - AutoLibrary",
                    "用户配置文件读取发生错误 ! :\n"\
                    "无法从选择的用户配置文件中加载数据 ! :\n"\
                    "可能选择了错误的配置文件类型"
                )

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
                exist_files.append(f"运行配置文件: \n{run_config_path}")
            if user_exists:
                exist_files.append(f"用户配置文件: \n{user_config_path}")
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
        self.initializeConfigToWidget("run", self.__config_data["run"])
        self.initializeConfigToWidget("user", self.__config_data["user"])

    @Slot()
    def onConfirmButtonClicked(
        self
    ):

        CurrentItem = self.UserTreeWidget.currentItem()
        if CurrentItem and CurrentItem.type() == ALUserTreeItemType.USER.value:
            self.UserTreeWidget.setCurrentItem(None)
        if self.saveConfigs(
            self.__config_paths["run"],
            self.__config_paths["user"]
        ):
            QMessageBox.information(
                self,
                "提示 - AutoLibrary",
                "配置文件保存成功 ! :\n"
                f"运行配置文件路径: \n{self.__config_paths['run']}\n"\
                f"用户配置文件路径: \n{self.__config_paths['user']}"
            )
        else:
            QMessageBox.warning(
                self,
                "警告 - AutoLibrary",
                "配置文件保存失败 !\n"
            )
        self.close()

    @Slot()
    def onCancelButtonClicked(
        self
    ):

        self.close()