#!/usr/bin/env python3

"""QLineEdit that can capture keyboard shortcuts."""

from qtpy import QtCore, QtGui, QtWidgets


class ShortcutLineEdit(QtWidgets.QLineEdit):
    """A QLineEdit specifically for capturing keyboard shortcuts."""

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Override the widget's keyPressEvent method."""
        assert event.type() == QtCore.QEvent.Type.KeyPress
        key = event.key()
        if key in (
            QtCore.Qt.Key.Key_unknown,
            QtCore.Qt.Key.Key_Control,
            QtCore.Qt.Key.Key_Shift,
            QtCore.Qt.Key.Key_Alt,
            QtCore.Qt.Key.Key_Meta,
        ):
            return
        if key == QtCore.Qt.Key.Key_Backspace:
            super().keyPressEvent(event)
            return
        modifiers = event.modifiers()
        combiner = QtCore.QKeyCombination(QtCore.Qt.Key(key))
        if modifiers & QtCore.Qt.KeyboardModifier.ControlModifier:
            combiner = QtCore.QKeyCombination(
                QtCore.Qt.Modifier.CTRL, QtCore.Qt.Key(key)
            )
        if modifiers & QtCore.Qt.KeyboardModifier.ShiftModifier:
            combiner = QtCore.QKeyCombination(
                QtCore.Qt.Modifier.SHIFT, QtCore.Qt.Key(key)
            )
        if modifiers & QtCore.Qt.KeyboardModifier.AltModifier:
            combiner = QtCore.QKeyCombination(
                QtCore.Qt.Modifier.ALT, QtCore.Qt.Key(key)
            )
        if modifiers & QtCore.Qt.KeyboardModifier.MetaModifier:
            combiner = QtCore.QKeyCombination(
                QtCore.Qt.Modifier.META, QtCore.Qt.Key(key)
            )
        sequence = QtGui.QKeySequence(combiner.toCombined())
        self.setText(sequence.toString(QtGui.QKeySequence.SequenceFormat.PortableText))
        event.accept()
