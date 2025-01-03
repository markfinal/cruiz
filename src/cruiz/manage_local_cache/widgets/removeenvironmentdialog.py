#!/usr/bin/env python3

"""Dialog for removing an environment variable."""

from cruiz.pyside6.local_cache_remove_environment import Ui_RemoveEnvironmentDialog

from qtpy import QtCore, QtWidgets


class RemoveEnvironmentDialog(QtWidgets.QDialog):
    """Dialog for removing an environment variable from the collection used to run Conan commands."""  # noqa: E501

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        """Initialise a RemoveEnvironmentDialog."""
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._ui = Ui_RemoveEnvironmentDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.name.textChanged.connect(self._updated)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(False)
        self.name: str = ""

    def _set_name(self) -> None:
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        self._ui.name.setText(sender_lineedit.text())

    def _updated(self) -> None:
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(bool(self._ui.name.text()))

    def accept(self) -> None:
        """Override the accept dialog method."""
        self.name = self._ui.name.text()
        super().accept()
