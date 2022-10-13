#!/usr/bin/env python3

"""
Dialog for adding an environment variable
"""

from dataclasses import dataclass

from qtpy import QtCore, QtGui, QtWidgets, PYSIDE2

from cruiz.commands.context import ConanContext

if PYSIDE2:
    from cruiz.pyside2.local_cache_add_environment import Ui_AddEnvironmentDialog

    QAction = QtWidgets.QAction
else:
    from cruiz.pyside6.local_cache_add_environment import Ui_AddEnvironmentDialog

    QAction = QtGui.QAction


@dataclass
class KeyValuePair:
    """
    Representation of a key-value pair
    """

    key: str
    value: str


class AddEnvironmentDialog(QtWidgets.QDialog):
    """
    Dialog for adding an environment key-value pair to the local cache.
    """

    def __init__(self, context: ConanContext, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._ui = Ui_AddEnvironmentDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        conan_environment_menu = QtWidgets.QMenu("Conan environment variables", self)
        for key, _ in context.get_conan_config_environment_variables().items():
            key_action = QAction(key, self)
            key_action.triggered.connect(self._set_name)
            conan_environment_menu.addAction(key_action)
        conan_environment_menu.addSeparator()
        # TODO: CONAN_V2_MODE is obsolete
        conan_v2_mode_action = QAction("CONAN_V2_MODE", self)
        conan_v2_mode_action.triggered.connect(self._set_name)  # type: ignore
        conan_environment_menu.addAction(conan_v2_mode_action)
        self._ui.name.set_custom_menu(conan_environment_menu)
        self._ui.name.textChanged.connect(self._updated)
        self._ui.value.textChanged.connect(self._updated)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self._name: str = ""
        self._value: str = ""

    def _set_name(self) -> None:
        self._ui.name.setText(self.sender().text())

    def _updated(self) -> None:
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
            bool(self._ui.name.text() and self._ui.value.text())
        )

    def accept(self) -> None:
        self._name = self._ui.name.text()
        self._value = self._ui.value.text()
        super().accept()

    @property
    def environment_variable(self) -> KeyValuePair:
        """
        Get the environment key-value pair just added.
        """
        return KeyValuePair(self._name, self._value)
