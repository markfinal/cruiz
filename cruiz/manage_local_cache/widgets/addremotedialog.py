#!/usr/bin/env python3

"""
Dialog for adding a new remote.
"""

from functools import partial
import typing

from qtpy import QtCore, QtGui, QtWidgets, PYSIDE2

import validators

from cruiz.interop.pod import ConanRemote

from cruiz.settings.managers.recentconanremotes import RecentConanRemotesSettingsReader

if PYSIDE2:
    from cruiz.pyside2.local_cache_add_remote import Ui_AddRemoteDialog

    QAction = QtWidgets.QAction
else:
    from cruiz.pyside6.local_cache_add_remote import Ui_AddRemoteDialog

    QAction = QtGui.QAction


class AddRemoteDialog(QtWidgets.QDialog):
    """
    Dialog for adding a new remote.
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._ui = Ui_AddRemoteDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        recent_remotes_menu = QtWidgets.QMenu("Recent remotes", self)
        with RecentConanRemotesSettingsReader() as settings:
            recent_remote_urls = settings.urls.resolve()
        if recent_remote_urls:
            for remote in recent_remote_urls:
                remote_action = QAction(remote, self)
                remote_action.triggered.connect(partial(self._set_remote_url, remote))
                recent_remotes_menu.addAction(remote_action)
        else:
            recent_remotes_menu.setEnabled(False)
        self._ui.url.set_custom_menu(recent_remotes_menu)
        self._ui.url.textChanged.connect(self._updated)
        self._ui.name.textChanged.connect(self._updated)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).clicked.connect(
            self.accept
        )
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Cancel).clicked.connect(
            self.reject
        )
        self._new_remote: typing.Optional[ConanRemote] = None

    def _set_remote_url(self, url: str) -> None:
        self._ui.url.setText(url)

    def _updated(self, path: str) -> None:
        # pylint: disable=unused-argument
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
            bool(
                self._ui.name.text()
                and self._ui.url.text()
                and validators.url(self._ui.url.text())
            )
        )

    def accept(self) -> None:
        self._new_remote = ConanRemote(self._ui.name.text(), self._ui.url.text(), True)
        super().accept()

    @property
    def new_remote(self) -> ConanRemote:
        """
        Details of the new remote just added.
        """
        assert self._new_remote
        return self._new_remote
