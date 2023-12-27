#!/usr/bin/env python3

"""
Dialog to show cruiz information
"""

import sys
import typing

from qtpy import QtCore, QtGui, QtWidgets

from cruiz.version import get_version

from cruiz.pyside6.about_dialog import Ui_AboutCruiz


class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self._ui = Ui_AboutCruiz()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.cruiz.setPixmap(
            QtGui.QPixmap(":/cruiz.png").scaled(64, 64, QtCore.Qt.KeepAspectRatio)
        )
        self._ui.version.setText(f"Version: {get_version()}")
        self._ui.python.setText(f"Python executable: {sys.executable}")
        self._ui.python_version.setText(f"Python version: {sys.version}")
        self._ui.pyside_version.setText(f"PySide version: {QtCore.__version__}")
