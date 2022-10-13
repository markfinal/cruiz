#!/usr/bin/env python3

"""
Reveal on a filesystem

Based on the C++ code in
https://github.com/qt-creator/qt-creator/blob/master/src/plugins/coreplugin/fileutils.cpp, # noqa: E501
FileUtils::showInGraphicalShell
"""

import os
import platform

from qtpy import QtCore, QtWidgets


def _run_apple_script(command: str) -> None:
    script_args = ["-e", command]
    QtCore.QProcess.execute("/usr/bin/osascript", script_args)


def _run_apple_script_activate_application(app_name: str) -> None:
    _run_apple_script(f'tell application "{app_name}" to activate')


def _use_finder(file_info: QtCore.QFileInfo) -> None:
    app = "Finder"
    _run_apple_script(
        f'tell application "{app}" to reveal POSIX file '
        f'"{file_info.canonicalFilePath()}"'
    )
    _run_apple_script_activate_application(app)


def _use_explorer(file_info: QtCore.QFileInfo) -> None:
    explorer_path = QtCore.QStandardPaths.findExecutable("explorer.exe")
    script_args = [QtCore.QDir.toNativeSeparators(file_info.canonicalFilePath())]
    QtCore.QProcess.startDetached(explorer_path, script_args)


def _use_xdg_open(file_info: QtCore.QFileInfo) -> None:
    xdg_open_path = QtCore.QStandardPaths.findExecutable("xdg-open")
    if not xdg_open_path:
        QtWidgets.QMessageBox.critical(
            None,  # type: ignore
            "Cannot reveal path",
            "Unable to find the path to xdg-open",
        )
        return
    script_args = [file_info.canonicalFilePath()]
    QtCore.QProcess.startDetached(xdg_open_path, script_args)


# TODO: pathlib instead?
def reveal_on_filesystem(path: str) -> None:
    """
    Reveal the path in a filesystem GUI
    """
    file_info = QtCore.QFileInfo(path)
    if not file_info.exists():
        QtWidgets.QMessageBox.critical(
            None, "Cannot reveal path", f"Path '{path}' does not exist"  # type: ignore
        )
        return
    if platform.system() == "Darwin":
        _use_finder(file_info)
    elif platform.system() == "Windows":
        _use_explorer(file_info)
    elif platform.system() == "Linux":
        _use_xdg_open(file_info)
    else:
        raise RuntimeError(f"Unrecognised platform {platform.system()}")


def open_terminal_at(path: str) -> None:
    """
    Open a terminal at the given directory path.
    """
    # cannot use QProcess here, as it starts a shell in-pr5ocess, even if called
    # with startDetached
    file_info = QtCore.QFileInfo(path)
    if not file_info.exists():
        QtWidgets.QMessageBox.critical(
            None,  # type: ignore
            "Cannot open terminal at path",
            f"Path '{path}' does not exist",
        )
        return
    if platform.system() == "Darwin":
        app = "Terminal"
        _run_apple_script(
            f'tell application "{app}" to do script "cd " & '
            f'"{file_info.canonicalFilePath()}"'
        )
        _run_apple_script_activate_application(app)
    elif platform.system() == "Windows":
        os.system(
            "start /D "
            f"{QtCore.QDir.toNativeSeparators(file_info.canonicalFilePath())}"
        )
    elif platform.system() == "Linux":
        if [key for key in os.environ if "GNOME" in key]:
            # TODO: centos does complain that this is deprecated, and to use gio open
            # instead but am not sure how to detect that
            # trailing $SHELL is to keep the new terminal open
            os.system(
                "gnome-terminal -- /bin/bash -c "
                f"'cd {file_info.canonicalFilePath()}; $SHELL'"
            )
        else:
            QtWidgets.QMessageBox.critical(
                None,  # type: ignore
                "Cannot open terminal at path",
                "Unable to detect window manager",
            )
    else:
        raise RuntimeError(f"Unrecognised platform {platform.system()}")
