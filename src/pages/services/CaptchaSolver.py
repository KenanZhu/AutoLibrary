# -*- coding: utf-8 -*-
"""
Copyright (c) 2026 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import base64
import queue

import ddddocr
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
)

from base.MsgBase import MsgBase
from pages.LoginPage import LoginPage


class CaptchaSolver(MsgBase):

    def __init__(
        self,
        input_queue: queue.Queue,
        output_queue: queue.Queue,
    ) -> None:

        super().__init__(input_queue, output_queue)
        self._ocr = ddddocr.DdddOcr()

    def _autoRecognize(
        self,
        login_page: LoginPage,
    ) -> str:

        try:
            img_src = login_page.getCaptchaImageSrc()
            base64_str = img_src.split(',', 1)[1]
            captcha_img = base64.b64decode(base64_str)
            captcha_text = self._ocr.classification(captcha_img)
            captcha_text = ''.join(filter(str.isalnum, captcha_text)).lower()
            self._showTrace(f"识别到验证码为 : '{captcha_text}'", 20, no_log=True)
            if len(captcha_text) != 4:
                self._showLog("识别到的验证码长度不等于 4 个字符 !", self.TraceLevel.WARNING)
                raise Exception("识别到的验证码长度不等于 4 个字符 !")
            return captcha_text
        except (NoSuchElementException, TimeoutException) as e:
            self._showTrace(f"验证码识别失败 ! : {e}", self.TraceLevel.ERROR)
            return ""
        except (ValueError, OSError) as e:
            self._showTrace(f"验证码识别失败 ! : {e}", self.TraceLevel.ERROR)
            return ""
        except Exception as e:
            self._showTrace(f"验证码识别失败 ! : {e}", self.TraceLevel.ERROR)
            return ""

    def _manualRecognize(
        self,
    ) -> str:

        try:
            self._showMsg("请输入验证码:")
            captcha_text = self._waitMsg(timeout=15)
            self._showTrace(f"输入的验证码为 : '{captcha_text}'", 20, no_log=True)
            if len(captcha_text) != 4:
                self._showLog("输入的验证码长度不等于 4 个字符 !", self.TraceLevel.WARNING)
                raise Exception("输入的验证码长度不等于 4 个字符 !")
            return captcha_text
        except ValueError as e:
            self._showTrace(f"输入验证码失败 ! : {e}", self.TraceLevel.ERROR)
            return ""
        except Exception as e:
            self._showTrace(f"输入验证码失败 ! : {e}", self.TraceLevel.ERROR)
            return ""

    def solveCaptcha(
        self,
        login_page: LoginPage,
        auto_captcha: bool = True,
    ) -> str:

        max_attempts = 3
        for _ in range(max_attempts):
            if auto_captcha:
                captcha_text = self._autoRecognize(login_page)
            else:
                self._showTrace("用户未配置自动识别验证码, 请手动输入验证码 !", 20, no_log=True)
                captcha_text = self._manualRecognize()
            if captcha_text:
                return captcha_text
            else:
                if not login_page.refreshCaptcha():
                    return ""
        self._showTrace(
            f"验证码识别失败 {max_attempts} 次, 达到最大尝试次数 !",
            self.TraceLevel.WARNING,
        )
        return ""
