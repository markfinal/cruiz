#!/usr/bin/env python3

"""
Remote browser page
"""

import typing

from qtpy import QtCore, QtGui, QtWidgets

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
        return remote_browser._log_details  # type: ignore[attr-defined]

    @property
    def _context(self) -> ConanContext:
        stacked_widget = self.parent()
        dock_contents = stacked_widget.parent()
        remote_browser = dock_contents.parent()
        return remote_browser._context  # type: ignore[attr-defined]

    @property
    def _revisions_enabled(self) -> bool:
        stacked_widget = self.parent()
        assert isinstance(stacked_widget, QtWidgets.QStackedWidget)
        pkgref_page = stacked_widget.widget(0)
        return pkgref_page._revs_enabled  # type: ignore[attr-defined]

    def _on_pkgref_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        copy_action = QtGui.QAction("Copy to clipboard", self)
        copy_action.triggered.connect(self._on_copy_pkgref_to_clip)  # type: ignore[attr-defined] # noqa: E501
        menu.addAction(copy_action)
        sender_label = self.sender()
        assert isinstance(sender_label, QtWidgets.QLabel)
        menu.exec_(sender_label.mapToGlobal(position))

    def _on_selected_pkgref_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        copy_action = QtGui.QAction("Copy to clipboard", self)
        copy_action.triggered.connect(self._on_copy_selected_pkgref_to_clip)
        menu.addAction(copy_action)
        sender_tableview = self.sender()
        assert isinstance(sender_tableview, QtWidgets.QTableView)
        menu.exec_(sender_tableview.mapToGlobal(position))

    def _on_copy_selected_pkgref_to_clip(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self.package_reference)  # type: ignore[attr-defined] # noqa: E501

    def _open_start(self) -> None:
        stacked_widget = self.parent()
        assert isinstance(stacked_widget, QtWidgets.QStackedWidget)
        stacked_widget.setCurrentIndex(0)
        stacked_widget.widget(0).invalidate()  # type: ignore[attr-defined]

    def _open_previous_page(self) -> None:
        parent_stackedwidget = self.parent()
        assert isinstance(parent_stackedwidget, QtWidgets.QStackedWidget)
        parent_stackedwidget.setCurrentIndex(self.page_index - 1)

    def _open_next_page(self) -> None:
        parent_stackedwidget = self.parent()
        assert isinstance(parent_stackedwidget, QtWidgets.QStackedWidget)
        parent_stackedwidget.setCurrentIndex(self.page_index + 1)

    @property
    def _previous_page(self) -> QtWidgets.QWidget:
        stacked_widget = self.parent()
        assert isinstance(stacked_widget, QtWidgets.QStackedWidget)
        if self._revisions_enabled:
            return stacked_widget.widget(self.page_index - 1)
        return stacked_widget.widget(self.page_index - 2)

    @property
    def _previous_pkgref(self) -> str:
        return self._previous_page.package_reference  # type: ignore[attr-defined] # noqa: E501
