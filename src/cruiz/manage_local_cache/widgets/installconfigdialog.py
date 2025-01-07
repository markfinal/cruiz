#!/usr/bin/env python3

"""Dialog for installing a new Conan config."""

from __future__ import annotations

import typing
from functools import partial

from PySide6 import QtCore, QtGui, QtWidgets

import cruiz.workers.api as workers_api
from cruiz.interop.commandparameters import CommandParameters
from cruiz.pyside6.local_cache_install_config import Ui_InstallConfigDialog
from cruiz.settings.managers.recentconanconfigs import (
    RecentConanConfigSettings,
    RecentConanConfigSettingsReader,
    RecentConanConfigSettingsWriter,
)

if typing.TYPE_CHECKING:
    from cruiz.commands.context import ConanContext


class InstallConfigDialog(QtWidgets.QDialog):
    """Dialog for installing a new Conan config onto the local cache."""

    def __init__(self, context: ConanContext, parent: QtWidgets.QWidget) -> None:
        """Initialise an InstallConfigDialog."""
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._ui = Ui_InstallConfigDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._context = context
        recent_config_paths_actions: typing.List[QtGui.QAction] = []
        with RecentConanConfigSettingsReader() as settings:
            config_paths = settings.paths.resolve()
        if config_paths:
            for path in config_paths:
                path_action = QtGui.QAction(path, self)
                path_action.triggered.connect(partial(self._set_url, path))
                recent_config_paths_actions.append(path_action)
        self._ui.pathOrUrl.add_submenu_actions(
            "Recent config paths", recent_config_paths_actions
        )
        self._ui.pathOrUrl.textChanged.connect(self._path_updated)
        self._ui.installButton.setEnabled(False)
        self._ui.installButton.clicked.connect(self._install)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        ).clicked.connect(self._cancel)

    def _set_url(self, path: str) -> None:
        self._ui.pathOrUrl.setText(path)

    def _path_updated(self, path: str) -> None:
        self._ui.installButton.setEnabled(bool(path))

    def _install(self) -> None:
        self._ui.progressBar.setMaximum(0)
        params = CommandParameters("install_config", workers_api.configinstall.invoke)
        named_args = params.named_arguments
        named_args["pathOrUrl"] = self._ui.pathOrUrl.text().strip()
        if self._ui.gitBranch.text():
            named_args["gitBranch"] = self._ui.gitBranch.text().strip()
        if self._ui.sourceFolder.text():
            named_args["sourceFolder"] = self._ui.sourceFolder.text().strip()
        if self._ui.targetFolder.text():
            named_args["targetFolder"] = self._ui.targetFolder.text().strip()
        self._context.install_config(params, self._install_complete)

    def _install_complete(self, result: typing.Any, exception: typing.Any) -> None:
        # pylint: disable=unused-argument
        self._ui.progressBar.setMaximum(1)
        if exception:
            QtWidgets.QMessageBox.critical(
                self,
                "Local cache config install failure",
                str(exception),
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.NoButton,
            )
            return
        with RecentConanConfigSettingsReader() as settings:
            config_paths = settings.paths.resolve()
        if self._ui.pathOrUrl.text() not in config_paths:
            settings = RecentConanConfigSettings()
            new_paths = config_paths + [self._ui.pathOrUrl.text()]
            settings.paths = new_paths  # type: ignore[assignment]
            RecentConanConfigSettingsWriter().sync(settings)
        self.accept()

    def _cancel(self) -> None:
        self._ui.progressBar.setMaximum(1)
        self._context.cancel()
        self.reject()
