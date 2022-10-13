#!/usr/bin/env python3

"""
QLineEdit subclass that has a custom context menu
"""

from qtpy import QtGui, QtWidgets


class LineEditWithCustomContextMenu(QtWidgets.QLineEdit):
    """
    Subclass allowing a custom context menu to be appended to the standard menu.
    """

    def set_custom_menu(self, menu: QtWidgets.QMenu) -> None:
        """
        Set the custom menu on this widget
        """
        # pylint: disable=attribute-defined-outside-init
        self._custom_menu = menu

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = self.createStandardContextMenu()
        if self._custom_menu:
            menu.addSeparator()
            menu.addMenu(self._custom_menu)
        menu.exec_(event.globalPos())
