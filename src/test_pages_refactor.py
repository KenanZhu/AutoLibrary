# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.

AutoLibrary 真实运行测试脚本。
在 venv 中运行:
    py -3 test_pages_refactor.py [--mode MODE]

MODE 可选值 (默认 1):
  1 = 只预约
  2 = 只签到
  3 = 预约 + 签到
  4 = 只续约
  7 = 全部 (预约 + 签到 + 续约)
"""
import os
import sys
import argparse

SRC = os.path.dirname(os.path.abspath(__file__))
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def getAppConfigDir() -> str:
    appData = os.environ.get("APPDATA", "")
    if not appData:
        appData = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(appData, "AutoLibrary", "configs")


def main():
    parser = argparse.ArgumentParser(description="AutoLibrary 真实运行测试")
    parser.add_argument(
        "--mode", type=int, default=1,
        help="运行模式 bitmask: 1=预约 2=签到 4=续约 (默认 1)"
    )
    parser.add_argument(
        "--group", type=int, default=0,
        help="只运行第 N 个启用的任务组 (0=全部, 默认 0)"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="使用 headless 模式运行浏览器"
    )
    args = parser.parse_args()

    # ---- 1. 初始化 ConfigManager ----
    from managers.config.ConfigManager import instance as configInstance
    from managers.config.ConfigUtils import ConfigUtils
    from utils.JSONReader import JSONReader

    configDir = getAppConfigDir()
    if not os.path.isdir(configDir):
        print(f"[FAIL] 配置目录不存在: {configDir}")
        print("请先启动一次 AutoLibrary GUI 以生成配置文件。")
        return 1

    try:
        configInstance(configDir)
    except ValueError:
        pass

    configPaths = ConfigUtils.getAutomationConfigPaths()
    runPath = configPaths.get("run")
    userPath = configPaths.get("user")

    if not runPath or not os.path.isfile(runPath):
        print(f"[FAIL] run.json 不存在: {runPath}")
        return 1
    if not userPath or not os.path.isfile(userPath):
        print(f"[FAIL] user.json 不存在: {userPath}")
        return 1

    print(f"[INFO] run  : {runPath}")
    print(f"[INFO] user : {userPath}")

    # ---- 2. 加载配置 ----
    runConfig = JSONReader(runPath).data()
    userConfig = JSONReader(userPath).data()

    if args.mode is not None:
        runConfig["mode"]["run_mode"] = args.mode
    if args.headless:
        runConfig["web_driver"]["headless"] = True

    groups = userConfig.get("groups", [])
    if not groups:
        print("[FAIL] user.json 中没有任务组")
        return 1

    print(f"[INFO] 运行模式: {runConfig['mode']['run_mode']}")
    if args.headless:
        print("[INFO] Headless 模式已启用")

    # ---- 3. 创建 AutoLib 并运行 ----
    from pages.AutoLibPages import AutoLibPages
    import queue
    import threading

    for gi, group in enumerate(groups):
        if args.group > 0 and gi + 1 != args.group:
            continue
        if not group.get("enabled", True):
            print(f"[SKIP] 任务组 {gi + 1} '{group.get('name', '未命名')}' 已禁用")
            continue

        users = group.get("users", [])
        enabledUsers = [u for u in users if u.get("enabled", True)]
        if not enabledUsers:
            print(f"[SKIP] 任务组 {gi + 1} 没有启用的用户")
            continue

        print(f"\n{'=' * 60}")
        print(f"任务组 {gi + 1}/{len(groups)}: '{group.get('name', '未命名')}'")
        print(f"启用的用户: {len(enabledUsers)}/{len(users)}")
        print(f"{'=' * 60}")

        outputQueue = queue.Queue()
        stopConsumer = threading.Event()
        traceLines = []

        def consumeTrace():
            while not stopConsumer.is_set():
                try:
                    msg = outputQueue.get(timeout=0.3)
                    traceLines.append(msg)
                    print(msg)
                except queue.Empty:
                    continue

        consumer = threading.Thread(target=consumeTrace, daemon=True)
        consumer.start()

        try:
            autoLib = AutoLibPages(
                input_queue=queue.Queue(),
                output_queue=outputQueue,
                run_config=runConfig,
            )
            autoLib.run({"users": enabledUsers})
            autoLib.close()
        except Exception as e:
            print(f"[FAIL] 运行异常: {e}")
            import traceback
            traceback.print_exc()
            return 1
        finally:
            stopConsumer.set()
            consumer.join(timeout=2)

    print("\n[OK] 测试完成")
    return 0


if __name__ == "__main__":
    sys.exit(main())
