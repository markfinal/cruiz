#!/usr/bin/env python3

"""Dialog for adding an environment variable."""

from __future__ import annotations

import typing
from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets

import cruiz.globals
from cruiz.pyside6.local_cache_add_environment import Ui_AddEnvironmentDialog

if typing.TYPE_CHECKING:
    from cruiz.commands.context import ConanContext


@dataclass
class KeyValuePair:
    """Representation of a key-value pair."""

    key: str
    value: str


class AddEnvironmentDialog(QtWidgets.QDialog):
    """Dialog for adding an environment key-value pair to the local cache."""

    def __init__(self, context: ConanContext, parent: QtWidgets.QWidget) -> None:
        """Initialise an AddEnvironmentDialog."""
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._ui = Ui_AddEnvironmentDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        conan_environment_actions: typing.List[QtGui.QAction] = []
        for key in context.get_conan_config_environment_variables():
            key_action = QtGui.QAction(key, self)
            key_action.triggered.connect(self._set_name)
            conan_environment_actions.append(key_action)
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            # TODO: CONAN_V2_MODE is obsolete
            conan_v2_mode_action = QtGui.QAction("CONAN_V2_MODE", self)
            conan_v2_mode_action.triggered.connect(self._set_name)
            conan_environment_actions.append(conan_v2_mode_action)
        self._ui.name.add_submenu_actions(
            "Conan environment variables", conan_environment_actions
        )
        self._ui.name.textChanged.connect(self._updated)
        self._ui.value.textChanged.connect(self._updated)
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(False)
        self._name: str = ""
        self._value: str = ""

    def _set_name(self) -> None:
        sender_action = self.sender()
        assert isinstance(sender_action, QtGui.QAction)
        self._ui.name.setText(sender_action.text())

    def _updated(self) -> None:
        self._ui.buttonBox.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(bool(self._ui.name.text() and self._ui.value.text()))

    def accept(self) -> None:
        """Override the accept dialog method."""
        self._name = self._ui.name.text()
        self._value = self._ui.value.text()
        super().accept()

    @property
    def environment_variable(self) -> KeyValuePair:
        """Get the environment key-value pair just added."""
        return KeyValuePair(self._name, self._value)
