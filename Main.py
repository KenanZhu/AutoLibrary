# -*- coding: utf-8 -*-
"""
Copyright (c) 2025 KenanZhu.
All rights reserved.

This software is provided "as is", without any warranty of any kind.
You may use, modify, and distribute this file under the terms of the MIT License.
See the LICENSE file for details.
"""
import sys

from PySide6.QtCore import QTranslator
from PySide6.QtWidgets import QApplication

from gui.ALMainWindow import ALMainWindow
from gui import AutoLibraryResource


def main():

    app = QApplication(sys.argv)
    translator = QTranslator()
    if translator.load(":/res/trans/translators/qtbase_zh_CN.ts"):
        app.installTranslator(translator)
    app.setStyle('Fusion')
    window = ALMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":

    main()