#!/usr/bin/env python3

"""Widget utilities."""

import platform
import typing

from PySide6 import QtCore, QtWidgets


def search_for_dir_options() -> QtWidgets.QFileDialog.Option:
    """Get standard file dialog options for directory searching."""
    options = QtWidgets.QFileDialog.Option.ShowDirsOnly
    if platform.system() == "Darwin":
        # have to use the non-native dialog on macOS, otherwise cannot browse
        # into an application bundle
        options = options | QtWidgets.QFileDialog.Option.DontUseNativeDialog
    return options


def search_for_file_options() -> QtWidgets.QFileDialog.Option:
    """Get standard file dialog options for file searching."""
    options = QtWidgets.QFileDialog.Option(0)
    if platform.system() == "Darwin":
        # have to use the non-native dialog on macOS, otherwise cannot browse
        # into an application bundle
        options = options | QtWidgets.QFileDialog.Option.DontUseNativeDialog
    return options


def clear_widgets_from_layout(layout: QtWidgets.QLayout) -> None:
    """
    Clear all widgets from a layout.

    Does not take child layouts into account.
    """
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)
        assert item is not None
        item.widget().setParent(None)


class BlockSignals:
    """
    Use instances of this in with statements, that block and restore signals to the provided Qt object in the initialiser.

    These can be nested.

    Returns the object being blocked, for reuse in the scope, as the expression used to obtain the object may have been complex.
    """  # noqa: E501

    def __init__(self, qt_object: QtCore.QObject) -> None:
        """Initialise a BlockSignsl."""
        self._object = qt_object

    def __enter__(self) -> QtCore.QObject:
        """Enter a context manager with a BlockSignals."""
        self._old_state = self._object.blockSignals(True)
        return self._object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> None:
        """Exit a context manager with a BlockSignals."""
        self._object.blockSignals(self._old_state)
