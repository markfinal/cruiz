#!/usr/bin/env python3

"""Dialog for adding a new remote."""

import typing
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

from cruiz.interop.pod import ConanRemote
from cruiz.pyside6.local_cache_add_remote import Ui_AddRemoteDialog
from cruiz.settings.managers.recentconanremotes import RecentConanRemotesSettingsReader

import validators


class AddRemoteDialog(QtWidgets.QDialog):
    """Dialog for adding a new remote."""

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        """Initialise an AddRemoteDialog."""
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._ui = Ui_AddRemoteDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        recent_remotes_actions: typing.List[QtGui.QAction] = []
        with RecentConanRemotesSettingsReader() as settings:
            recent_remote_urls = settings.urls.resolve()
        if recent_remote_urls:
            for remote in recent_remote_urls:
                remote_action = QtGui.QAction(remote, self)
                remote_action.triggered.connect(partial(self._set_remote_url, remote))
                recent_remotes_actions.append(remote_action)
        self._ui.url.add_submenu_actions("Recent remotes", recent_remotes_actions)
        self._ui.url.textChanged.connect(self._updated)
        self._ui.name.textChanged.connect(self._updated)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).clicked.connect(self.accept)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(False)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        ).clicked.connect(self.reject)
        self._new_remote: typing.Optional[ConanRemote] = None

    def _set_remote_url(self, url: str) -> None:
        self._ui.url.setText(url)

    def _updated(self, path: str) -> None:
        # pylint: disable=unused-argument
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(
            bool(
                self._ui.name.text()
                and self._ui.url.text()
                and validators.url(self._ui.url.text())
            )
        )

    def accept(self) -> None:
        """Override the accept dialog method."""
        self._new_remote = ConanRemote(self._ui.name.text(), self._ui.url.text(), True)
        super().accept()

    @property
    def new_remote(self) -> ConanRemote:
        """Details of the new remote just added."""
        assert self._new_remote
        return self._new_remote
