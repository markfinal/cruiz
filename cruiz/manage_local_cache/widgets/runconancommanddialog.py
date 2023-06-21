#!/usr/bin/env python3

"""
Dialog for running a Conan command in a local cache.
"""

import typing

from qtpy import QtCore, QtWidgets

import cruiz.globals

from cruiz.commands.context import ConanContext, LogDetails
from cruiz.interop.commandparameters import CommandParameters

from cruiz.pyside6.local_cache_run_command_dialog import Ui_RunConanCommandDialog

import cruiz.workers.api as workers_api


class RunConanCommandDialog(QtWidgets.QDialog):
    """
    Dialog for adding an environment key-value pair to the local cache.
    """

    def __init__(self, context_name: str, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._ui = Ui_RunConanCommandDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._log_details = LogDetails(self._ui.log, self._ui.log, True, False, None)
        self._context = ConanContext(context_name, self._log_details)
        self._ui.arguments.textChanged.connect(self._on_arguments_changed)
        self._ui.run.clicked.connect(self._on_run)
        self._ui.run.setEnabled(False)

    def done(self, result: int) -> None:
        self._context.close()
        super().done(result)

    def _on_arguments_changed(self, text: str) -> None:
        self._ui.run.setEnabled(bool(text))

    def _on_run(self) -> None:
        args = self._ui.arguments.text().split()
        params = CommandParameters(args[0], workers_api.arbitrary.invoke)
        params.arguments.extend(args[1:])
        self._ui.arguments.setEnabled(False)
        self._ui.run.setEnabled(False)
        self._context.run_any_command(params, self._on_run_complete)

    def _on_run_complete(self, payload: typing.Any, exception: typing.Any) -> None:
        self._ui.arguments.setEnabled(True)
        self._ui.run.setEnabled(True)
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            # payload is always None
            pass
        else:
            self._log_details.stdout(payload)
            if exception:
                self._log_details.stderr("<font color='red'>Failed</font><br>")
            else:
                self._log_details.stdout("<font color='green'>Succeeded</font><br>")
