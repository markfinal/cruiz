#!/usr/bin/env python3

"""
Conan recipe find text dialog
"""

from qtpy import QtCore, QtWidgets, PYSIDE2

if PYSIDE2:
    from cruiz.pyside2.find_text_dialog import Ui_FindTextDialog
else:
    from cruiz.pyside6.find_text_dialog import Ui_FindTextDialog


class FindTextDialog(QtWidgets.QDialog):
    """
    Widget representing a Find dialog
    """

    search_forwards = QtCore.Signal(QtWidgets.QPlainTextEdit, str, bool, bool)
    search_backwards = QtCore.Signal(QtWidgets.QPlainTextEdit, str, bool, bool)

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        super().__init__(parent)
        self._ui = Ui_FindTextDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        find_next = QtWidgets.QPushButton("Find &next")
        find_prev = QtWidgets.QPushButton("Find &previous")
        find_next.clicked.connect(self._find_next)
        find_prev.clicked.connect(self._find_prev)
        self._ui.findTextButtonBox.addButton(
            find_next, QtWidgets.QDialogButtonBox.ActionRole
        )
        self._ui.findTextButtonBox.addButton(
            find_prev, QtWidgets.QDialogButtonBox.ActionRole
        )

    def _find_next(self) -> None:
        self.search_forwards.emit(
            self.parent(),
            self._ui.findTextSearch.text(),
            self._ui.findTextCaseSensitive.isChecked(),
            self._ui.findTextWraparound.isChecked(),
        )

    def _find_prev(self) -> None:
        self.search_backwards.emit(
            self.parent(),
            self._ui.findTextSearch.text(),
            self._ui.findTextCaseSensitive.isChecked(),
            self._ui.findTextWraparound.isChecked(),
        )
