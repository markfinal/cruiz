#!/usr/bin/env python3

"""Remote browser."""

import logging
import typing

from PySide6 import QtCore, QtGui, QtWidgets

from cruiz.commands.context import ConanContext
from cruiz.commands.logdetails import LogDetails
from cruiz.constants import DEFAULT_CACHE_NAME
from cruiz.pyside6.remote_browser import Ui_remotebrowser

logger = logging.getLogger(__name__)


class RemoteBrowserDock(QtWidgets.QDockWidget):
    """Dock widget for browsing Conan remotes."""

    def __del__(self) -> None:
        """Log when a RemoteBrowserDock is deleted."""
        logger.debug("-=%d", id(self))

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        """Initialise a RemoteBrowserDock."""
        logger.debug("+=%d", id(self))
        super().__init__(parent)
        self.setVisible(False)
        self._ui = Ui_remotebrowser()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.log.hide()
        self._ui.log.customContextMenuRequested.connect(self._log_context_menu)
        self._log_details = LogDetails(self._ui.log, None, True, False, None)
        self._log_details.logging.connect(self._ui.log.show)
        self._context = ConanContext(DEFAULT_CACHE_NAME, self._log_details)
        self._ui.pkgref.setup(self._ui)
        self._ui.rrev.setup(self._ui)
        self._ui.package_id.setup(self._ui)
        self._ui.prev.setup(self._ui)
        self._ui.pbinary.setup(self._ui)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Override the widget's showEvent method."""
        # although this looks like a no-op, it regenerates necessary resources
        self._context.change_cache(self._context.cache_name)
        super().showEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Override the widget's closeEvent method."""
        if self._context.is_busy:
            QtWidgets.QMessageBox.warning(
                self,
                "Remote browser cannot be closed",
                "Commands are still running. Cannot close remote browser.",
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.NoButton,
            )
            event.ignore()
            return
        self._context.close()
        super().closeEvent(event)

    def cleanup(self) -> None:
        """Clean up the widget."""
        self._ui.stackedWidget.currentWidget().on_cancel()  # type: ignore[attr-defined]
        self._log_details.stop()
        self._context.close()

    def on_local_cache_modified(self, cache_name: str) -> None:
        """Call when a local cache has been changed upstream."""
        self._ui.pkgref.refresh_local_cache_names()
        if cache_name == self._context.cache_name:
            self._ui.pkgref.on_local_cache_change(cache_name)
            self._ui.stackedWidget.setCurrentWidget(self._ui.pkgref)
            self._clear_log()

    def _log_context_menu(self, position: QtCore.QPoint) -> None:
        sender_plaintextedit = self.sender()
        assert isinstance(sender_plaintextedit, QtWidgets.QPlainTextEdit)
        menu = sender_plaintextedit.createStandardContextMenu(position)
        menu.addSeparator()
        clear_action = QtGui.QAction("Clear", self)
        clear_action.triggered.connect(self._clear_log)
        menu.addAction(clear_action)
        menu.exec_(sender_plaintextedit.viewport().mapToGlobal(position))

    def _clear_log(self) -> None:
        self._ui.log.clear()
        self._ui.log.hide()
