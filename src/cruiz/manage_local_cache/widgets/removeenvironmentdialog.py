#!/usr/bin/env python3

"""
Dialog for removing an environment variable
"""

from qtpy import QtCore, QtWidgets

from cruiz.pyside6.local_cache_remove_environment import Ui_RemoveEnvironmentDialog


class RemoveEnvironmentDialog(QtWidgets.QDialog):
    """
    Dialog for removing an environment variable from the collection used to run
    Conan commands
    """

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._ui = Ui_RemoveEnvironmentDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.name.textChanged.connect(self._updated)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self.name: str = ""

    def _set_name(self) -> None:
        self._ui.name.setText(self.sender().text())

    def _updated(self) -> None:
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
            bool(self._ui.name.text())
        )

    def accept(self) -> None:
        self.name = self._ui.name.text()
        super().accept()
