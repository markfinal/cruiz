#!/usr/bin/env python3

"""
The Qt application
"""

from __future__ import annotations

import typing

import qdarkstyle

from qtpy import QtCore, QtGui, QtWidgets

from cruiz.settings.ensuredefaultlocalcache import ensure_default_local_cache
from cruiz.settings.managers.fontpreferences import FontSettingsReader, FontUsage
from cruiz.settings.managers.generalpreferences import GeneralSettingsReader


class Application(QtWidgets.QApplication):
    """
    The application
    """

    def __init__(self, argv: typing.List[str]) -> None:
        super().__init__(argv)
        ensure_default_local_cache()
        self.setAttribute(QtCore.Qt.AA_DontUseNativeMenuBar)
        self.setWindowIcon(QtGui.QPixmap(":/cruiz.png"))
        self.default_font = QtWidgets.QApplication.font()
        self.on_preferences_updated()

    @staticmethod
    def instance() -> Application:
        """
        Get the application instance.
        qApp does the job already, but this returns it as an Application so that pylint
        can do static analysis on the additional methods on the subclass
        """
        # pylint: disable=undefined-variable
        return qApp  # type: ignore  # noqa: F821

    def on_preferences_updated(self) -> None:
        """
        Slot executed when preferences have reported an update.
        """
        with GeneralSettingsReader() as settings:
            use_dark_mode = settings.use_dark_mode.resolve()
        self.setStyleSheet(
            qdarkstyle.load_stylesheet_pyside2() if use_dark_mode else ""
        )
        with FontSettingsReader(FontUsage.UI) as settings:
            font_details = (settings.name.resolve(), settings.size.resolve())
        if font_details[0]:
            self.setFont(QtGui.QFont(*font_details))
        else:
            self.setFont(self.default_font)
