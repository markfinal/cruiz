#!/usr/bin/env python3

"""cruiz: Conan recipe user interface."""

import importlib.util
import logging
import os
import pathlib
import platform
import sys

from qtpy import QtCore, QtWidgets


CONAN_SPEC = importlib.util.find_spec("conans")
if CONAN_SPEC is None:
    QtWidgets.QApplication()
    QtWidgets.QMessageBox.critical(
        None,  # type: ignore[arg-type]
        "Conan unavailable",
        "Unable to locate the conan Python package in the current environment.\n"
        "Use pip install conan[==version].",
        button0=QtWidgets.QMessageBox.StandardButton.Ok,
        button1=QtWidgets.QMessageBox.StandardButton.NoButton,
    )
    sys.exit(-1)


logging.basicConfig(
    level=os.getenv("LOGLEVEL", "WARNING"),
    filename=os.getenv("LOGFILE", None),
)


logger = logging.getLogger(__name__)

import cruiz.pyside6.resources  # noqa: F401, E402, I100 # pylint: disable=unused-import
from cruiz.application import Application  # noqa: E402
from cruiz.mainwindow import MainWindow  # noqa: E402
from cruiz.settings.updatesettings import (  # noqa: E402
    update_settings_to_current_version,
)


def _are_resources_out_of_date() -> bool:
    current_dir = pathlib.Path(__file__).parent
    resources_dir = current_dir / "resources"
    if not resources_dir.exists():
        return False
    generated_files = [
        current_dir / "resources.py",
    ]
    if any(not path.exists() for path in generated_files):
        return False
    newest_generated_file = sorted(generated_files, key=os.path.getmtime, reverse=True)[
        0
    ]
    non_ui_resource_files = list(
        set(resources_dir.glob("*")) - set(resources_dir.glob("*.ui"))
    )
    newest_resource_file = sorted(
        non_ui_resource_files, key=os.path.getmtime, reverse=True
    )[0]
    input_mtime = os.path.getmtime(newest_resource_file)
    output_mtime = os.path.getmtime(newest_generated_file)
    return input_mtime > output_mtime


if _are_resources_out_of_date():
    QtWidgets.QApplication()
    QtWidgets.QMessageBox.critical(
        None,  # type: ignore[arg-type]
        "Resources",
        "Resources are out of date.\n" "Please build with python3 setup.py build",
        button0=QtWidgets.QMessageBox.StandardButton.Ok,
        button1=QtWidgets.QMessageBox.StandardButton.NoButton,
    )
    sys.exit(-1)


QtCore.QCoreApplication.setApplicationName("cruiz")
update_settings_to_current_version()

if platform.system() == "Darwin":
    os.environ["no_proxy"] = "*"


def _warning_message_filter(message: str) -> bool:
    if message.startswith("delivering touch release to same window"):
        return False
    if message.startswith("skipping QEventPoint("):
        return False
    if message.startswith("Populating font family aliases took"):
        return False
    if message.startswith("QTextCursor::setPosition: Position") and message.endswith(
        "out of range"
    ):
        return False
    return True


def _message_handler(
    mode: QtCore.QtMsgType, context: QtCore.QMessageLogContext, message: str
) -> None:
    # pylint: disable=unused-argument
    if mode == QtCore.QtMsgType.QtInfoMsg:
        logger.info(message)
    elif mode == QtCore.QtMsgType.QtWarningMsg:
        if _warning_message_filter(message):
            logger.warning(message)
    elif mode == QtCore.QtMsgType.QtCriticalMsg:
        logger.critical(message)
    elif mode == QtCore.QtMsgType.QtFatalMsg:
        raise RuntimeError(message)
    else:
        logger.debug(message)


def main() -> int:
    """Entry point."""
    QtCore.qInstallMessageHandler(_message_handler)

    QtWidgets.QApplication.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True
    )  # enable highdpi scaling
    QtWidgets.QApplication.setAttribute(
        QtCore.Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True
    )  # use highdpi icons
    QtWidgets.QApplication.setStyle("fusion")

    app = Application(sys.argv)
    window = MainWindow()
    window.showNormal()
    sys.exit(app.exec_())
