#!/usr/bin/env python3

"""Remote browser page."""

from __future__ import annotations

import abc
import typing

from PySide6 import QtCore, QtGui, QtWidgets

if typing.TYPE_CHECKING:
    from cruiz.commands.context import ConanContext
    from cruiz.commands.logdetails import LogDetails
    from cruiz.pyside6.remote_browser import Ui_remotebrowser
    from cruiz.remote_browser.remotebrowser import RemoteBrowserDock


class Page(QtWidgets.QWidget):
    """Base class for all pages shown in the remote browser."""

    def _base_setup(self, self_ui: Ui_remotebrowser, index: int) -> None:
        self._ui = self_ui
        self.page_index = index

    @property
    @abc.abstractmethod
    def package_reference(self) -> str:
        """Get the package reference with all details on the current page."""
        raise NotImplementedError()

    @abc.abstractmethod
    def _on_copy_pkgref_to_clip(self) -> None:
        """Copy the package reference with all details on the current page to the clipboard."""  # noqa: E501
        raise NotImplementedError()

    @property
    def _log_details(self) -> LogDetails:
        remote_browser: RemoteBrowserDock = self._ui.dockWidgetContents.parent()  # type: ignore[assignment]  # noqa: E501
        # pylint: disable=protected-access
        # TODO: this is non-public access as is just forwarding the parent's details
        return remote_browser._log_details

    @property
    def _context(self) -> ConanContext:
        remote_browser: RemoteBrowserDock = self._ui.dockWidgetContents.parent()  # type: ignore[assignment]  # noqa: E501
        # pylint: disable=protected-access
        # TODO: this is non-public access as is just forwarding the parent's details
        return remote_browser._context

    # TODO: does this belong in the parent?
    @property
    def _revisions_enabled(self) -> bool:
        # pylint: disable=protected-access
        # TODO: this is non-public access as is just forwarding the parent's details
        return self._ui.pkgref._revs_enabled

    def _on_pkgref_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        copy_action = QtGui.QAction("Copy to clipboard", self)
        copy_action.triggered.connect(self._on_copy_pkgref_to_clip)
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
        QtWidgets.QApplication.clipboard().setText(self.package_reference)

    def _open_start(self) -> None:
        self._ui.stackedWidget.setCurrentWidget(self._ui.pkgref)
        self._ui.pkgref.invalidate()

    @property
    def _previous_page(self) -> Page:
        index_offset = -1 if self._revisions_enabled else -2
        page = self._ui.stackedWidget.widget(self.page_index + index_offset)
        assert isinstance(page, Page)
        return page

    @property
    def _previous_pkgref(self) -> str:
        return self._previous_page.package_reference
