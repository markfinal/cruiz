#!/usr/bin/env python3

"""
Widget utilities
"""

import platform
import typing

from qtpy import QtCore, QtWidgets


def search_for_dir_options() -> QtWidgets.QFileDialog.Options:
    """
    Get standard file dialog options for directory searching.
    """
    options = QtWidgets.QFileDialog.ShowDirsOnly
    if platform.system() == "Darwin":
        # have to use the non-native dialog on macOS, otherwise cannot browse
        # into an application bundle
        options = options | QtWidgets.QFileDialog.DontUseNativeDialog
    return options


def search_for_file_options() -> QtWidgets.QFileDialog.Options:
    """
    Get standard file dialog options for file searching.
    """
    options = QtWidgets.QFileDialog.Options()
    if platform.system() == "Darwin":
        # have to use the non-native dialog on macOS, otherwise cannot browse
        # into an application bundle
        options = options | QtWidgets.QFileDialog.DontUseNativeDialog
    return options


def clear_widgets_from_layout(layout: QtWidgets.QLayout) -> None:
    """
    Clear all widgets from a layout.
    Does not take child layouts into account.
    """
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)  # type: ignore


class BlockSignals:
    """
    Use instances of this in with statements, that block and restore signals to the
    provided Qt object in the initialiser.

    These can be nested.

    Returns the object being blocked, for reuse in the scope, as the expression used to
    obtain the object may have been complex.
    """

    def __init__(self, qt_object: QtCore.QObject) -> None:
        self._object = qt_object

    def __enter__(self) -> QtCore.QObject:
        # pylint: disable=attribute-defined-outside-init
        self._old_state = self._object.blockSignals(True)
        return self._object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> None:
        self._object.blockSignals(self._old_state)
