#!/usr/bin/env python3

"""
Recipe command log window
"""

import os
import stat
import typing

from qtpy import QtCore, QtGui, QtWidgets, PYSIDE6

from cruiz.interop.commandparameters import CommandParameters

if PYSIDE6:
    QAction = QtGui.QAction
else:
    QAction = QtWidgets.QAction


class CommandListWidgetItem(QtWidgets.QListWidgetItem):
    """
    QListWidgetItem representing a Conan command
    """

    def __init__(
        self,
        parameters: CommandParameters,
        parent: typing.Optional[QtWidgets.QListWidget] = None,
    ) -> None:
        if parameters.cwd:
            expression = f"{parameters} (in {parameters.cwd})"
        else:
            expression = f"{parameters}"
        super().__init__(expression, parent, 1000)
        self.setData(0x0100, parameters)


class RecipeCommandHistoryWidget(QtWidgets.QListWidget):
    """
    QListWidget representing a history of Conan commands
    """

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemSelectionChanged.connect(self._selection_changed)
        self._export_bash_action = QAction("Export to file...", self)
        self._export_bash_action.triggered.connect(self._export_bash)
        self._export_zsh_action = QAction("Export to file...", self)
        self._export_zsh_action.triggered.connect(self._export_zsh)
        self._export_cmd_action = QAction("Export to file...", self)
        self._export_cmd_action.triggered.connect(self._export_cmd)
        self._copy_bash_to_clipboard_action = QAction("Copy to clipboard", self)
        self._copy_bash_to_clipboard_action.triggered.connect(
            self._copy_bash_to_clipboard
        )
        self._copy_zsh_to_clipboard_action = QAction("Copy to clipboard", self)
        self._copy_zsh_to_clipboard_action.triggered.connect(
            self._copy_zsh_to_clipboard
        )
        self._copy_cmd_to_clipboard_action = QAction("Copy to clipboard", self)
        self._copy_cmd_to_clipboard_action.triggered.connect(
            self._copy_cmd_to_clipboard
        )
        self._menu = QtWidgets.QMenu()
        self._menu.setEnabled(False)
        bash_menu = self._menu.addMenu("bash")
        bash_menu.insertAction(None, self._export_bash_action)  # type: ignore[arg-type]
        bash_menu.insertAction(
            None, self._copy_bash_to_clipboard_action  # type: ignore[arg-type]
        )
        zsh_menu = self._menu.addMenu("zsh")
        zsh_menu.insertAction(None, self._export_zsh_action)  # type: ignore[arg-type]
        zsh_menu.insertAction(
            None, self._copy_zsh_to_clipboard_action  # type: ignore[arg-type]
        )
        cmd_menu = self._menu.addMenu("Batch CMD")
        cmd_menu.insertAction(None, self._export_cmd_action)  # type: ignore[arg-type]
        cmd_menu.insertAction(
            None, self._copy_cmd_to_clipboard_action  # type: ignore[arg-type]
        )

    def _show_context_menu(self, position: QtCore.QPoint) -> None:
        if not any(self.selectedItems()):
            return
        self._menu.exec_(self.mapToGlobal(position))

    def _selection_changed(self) -> None:
        enabled = any(self.selectedItems())
        self._menu.setEnabled(enabled)

    def _export_bash(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Conan command as bash shell script",
            "",
            "Shell script (*.sh)",
        )
        if not filename:
            return
        item = self.selectedItems()[0]
        parameters = item.data(0x0100)
        with open(filename, "wt", encoding="utf-8") as shell_script:
            shell_script.write("#!/usr/bin/env bash\n")
            shell_script.write(f"{parameters.bash_expression.getvalue()}\n")
        os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)

    def _export_zsh(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Conan command as zsh shell script",
            "",
            "Shell script (*.sh)",
        )
        if not filename:
            return
        item = self.selectedItems()[0]
        parameters = item.data(0x0100)
        with open(filename, "wt", encoding="utf-8") as shell_script:
            shell_script.write("#!/usr/bin/env zsh\n")
            shell_script.write(f"{parameters.zsh_expression.getvalue()}\n")
        os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)

    def _export_cmd(self) -> None:
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Export Conan command as CMD Batch shell script",
            "",
            "Batch script (*.bat)",
        )
        if not filename:
            return
        item = self.selectedItems()[0]
        parameters = item.data(0x0100)
        with open(filename, "wt", encoding="utf-8") as shell_script:
            shell_script.write(f"{parameters.cmd_expression.getvalue()}\n")
        os.chmod(filename, os.stat(filename).st_mode | stat.S_IEXEC)

    def _copy_bash_to_clipboard(self) -> None:
        item = self.selectedItems()[0]
        parameters = item.data(0x0100)
        qApp.clipboard().setText(  # type: ignore  # noqa: F821
            parameters.bash_expression.getvalue()
        )

    def _copy_zsh_to_clipboard(self) -> None:
        item = self.selectedItems()[0]
        parameters = item.data(0x0100)
        qApp.clipboard().setText(  # type: ignore  # noqa: F821
            parameters.zsh_expression.getvalue()
        )

    def _copy_cmd_to_clipboard(self) -> None:
        item = self.selectedItems()[0]
        parameters = item.data(0x0100)
        qApp.clipboard().setText(  # type: ignore  # noqa: F821
            parameters.cmd_expression.getvalue()
        )
