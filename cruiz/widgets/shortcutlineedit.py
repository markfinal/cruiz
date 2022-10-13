#!/usr/bin/env python3

"""
QLineEdit that can capture keyboard shortcuts
"""

from qtpy import QtCore, QtGui, QtWidgets


class ShortcutLineEdit(QtWidgets.QLineEdit):
    """
    A QLineEdit specifically for capturing keyboard shortcuts
    """

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        assert event.type() == QtCore.QEvent.KeyPress
        key = event.key()
        if key in (  # type: ignore[comparison-overlap]
            QtCore.Qt.Key_unknown,
            QtCore.Qt.Key_Control,
            QtCore.Qt.Key_Shift,
            QtCore.Qt.Key_Alt,
            QtCore.Qt.Key_Meta,
        ):
            return
        if key == QtCore.Qt.Key_Backspace:  # type: ignore[comparison-overlap]
            super().keyPressEvent(event)
            return
        modifiers = event.modifiers()
        if modifiers & QtCore.Qt.ControlModifier:
            key += QtCore.Qt.CTRL  # type: ignore[operator]
        if modifiers & QtCore.Qt.ShiftModifier:
            key += QtCore.Qt.SHIFT  # type: ignore[operator]
        if modifiers & QtCore.Qt.AltModifier:
            key += QtCore.Qt.ALT  # type: ignore[operator]
        if modifiers & QtCore.Qt.MetaModifier:
            key += QtCore.Qt.META  # type: ignore[operator]
        sequence = QtGui.QKeySequence(key)
        self.setText(sequence.toString(QtGui.QKeySequence.PortableText))
        event.accept()
