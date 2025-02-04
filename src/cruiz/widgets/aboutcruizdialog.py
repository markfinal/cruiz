#!/usr/bin/env python3

"""Dialog to show cruiz information."""

import sys
import typing

from PySide6 import QtCore, QtGui, QtWidgets

from cruiz.pyside6.about_dialog import Ui_AboutCruiz
from cruiz.version import get_version


class AboutDialog(QtWidgets.QDialog):
    """Dialog showing about details of cruiz."""

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        """Initialise an AboutDialog."""
        super().__init__(parent)
        self._ui = Ui_AboutCruiz()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.cruiz.setPixmap(
            QtGui.QPixmap(":/cruiz.png").scaled(
                64, 64, QtCore.Qt.AspectRatioMode.KeepAspectRatio
            )
        )
        self._ui.version.setText(f"Version: {get_version()}")
        self._ui.python.setText(f"Python executable: {sys.executable}")
        self._ui.python_version.setText(f"Python version: {sys.version}")
        self._ui.pyside_version.setText(f"PySide version: {QtCore.qVersion()}")
