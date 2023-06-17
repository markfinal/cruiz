#!/usr/bin/env python3

"""
Dialog for adding extra profile directories
"""

import typing

from qtpy import QtCore, QtGui, QtWidgets

from cruiz.interop.pod import ExtraProfileDirectory
from cruiz.widgets.util import search_for_dir_options

from cruiz.pyside6.local_cache_add_profile_directory import (
    Ui_AddExtraProfileDirectoryDialog,
)


class AddExtraProfileDirectoryDialog(QtWidgets.QDialog):
    """
    Dialog for adding an extra profile directory.
    """

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._ui = Ui_AddExtraProfileDirectoryDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        self._ui.buttonBox.accepted.connect(self.accept)
        self._ui.buttonBox.rejected.connect(self.reject)
        self._ui.name.textChanged.connect(self._updated)
        self._ui.directory.textChanged.connect(self._updated)
        browse_for_profile_dir_action = QtGui.QAction(
            self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon), "", self
        )
        browse_for_profile_dir_action.triggered.connect(self._browse_for_profile_dir)
        self._ui.directory.addAction(
            browse_for_profile_dir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._extra: typing.Optional[ExtraProfileDirectory] = None

    def _updated(self, text: str) -> None:
        # pylint: disable=unused-argument
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(
            bool(self._ui.name.text() and self._ui.directory.text())
        )

    def accept(self) -> None:
        self._extra = ExtraProfileDirectory(
            self._ui.name.text(), self._ui.directory.text()
        )
        super().accept()

    def _browse_for_profile_dir(self) -> None:
        dir_found = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select extra profile directory",
            "",
            search_for_dir_options(),
        )
        if dir_found:
            self._ui.directory.setText(dir_found)

    @property
    def extra(self) -> ExtraProfileDirectory:
        """
        The extra profile directory added.
        """
        assert self._extra
        return self._extra
