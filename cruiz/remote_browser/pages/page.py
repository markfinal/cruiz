#!/usr/bin/env python3

"""
Remote browser page
"""

import typing

from qtpy import QtCore, QtGui, QtWidgets, PYSIDE2

if PYSIDE2:
    QAction = QtWidgets.QAction
else:
    QAction = QtGui.QAction

from cruiz.commands.context import ConanContext
from cruiz.commands.logdetails import LogDetails


class Page(QtWidgets.QWidget):
    """
    Base class for all pages shown in the remote browser
    """

    def _base_setup(self, self_ui: typing.Any, index: int) -> None:
        self._ui = self_ui
        self.page_index = index

    @property
    def _log_details(self) -> LogDetails:
        stacked_widget = self.parent()
        dock_contents = stacked_widget.parent()
        remote_browser = dock_contents.parent()
        return remote_browser._log_details

    @property
    def _context(self) -> ConanContext:
        stacked_widget = self.parent()
        dock_contents = stacked_widget.parent()
        remote_browser = dock_contents.parent()
        return remote_browser._context

    @property
    def _revisions_enabled(self) -> bool:
        stacked_widget = self.parent()
        pkgref_page = stacked_widget.widget(0)
        return pkgref_page._revs_enabled

    def _on_pkgref_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        copy_action = QAction("Copy to clipboard", self)
        copy_action.triggered.connect(self._on_copy_pkgref_to_clip)
        menu.addAction(copy_action)
        menu.exec_(self.sender().mapToGlobal(position))

    def _on_selected_pkgref_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        copy_action = QAction("Copy to clipboard", self)
        copy_action.triggered.connect(self._on_copy_selected_pkgref_to_clip)
        menu.addAction(copy_action)
        menu.exec_(self.sender().mapToGlobal(position))

    def _on_copy_selected_pkgref_to_clip(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self.package_reference)

    def _open_start(self) -> None:
        self.parent().setCurrentIndex(0)
        self.parent().widget(0).invalidate()

    def _open_previous_page(self) -> None:
        self.parent().setCurrentIndex(self.page_index - 1)

    def _open_next_page(self) -> None:
        self.parent().setCurrentIndex(self.page_index + 1)

    @property
    def _previous_page(self) -> QtWidgets.QWidget:
        if self._revisions_enabled:
            return self.parent().widget(self.page_index - 1)
        return self.parent().widget(self.page_index - 2)

    @property
    def _previous_pkgref(self) -> str:
        return self._previous_page.package_reference
