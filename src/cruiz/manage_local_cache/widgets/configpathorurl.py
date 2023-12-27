#!/usr/bin/env python3

"""
QLineEdit subclass that has a custom context menu
"""

import typing

from qtpy import QtGui, QtWidgets


class LineEditWithCustomContextMenu(QtWidgets.QLineEdit):
    """
    Subclass allowing a custom context menu to be appended to the standard menu.
    """

    def add_submenu_actions(
        self, submenu_name: str, actions: typing.List[QtGui.QAction]
    ) -> None:
        """
        Provide the name of a submenu and the QActions for it
        """
        self._submenu_name = submenu_name
        self._submenu_actions = actions

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        submenu = menu.addMenu(self._submenu_name)
        if self._submenu_actions:
            submenu.addActions(self._submenu_actions)
        else:
            submenu.setEnabled(False)

        menu.exec_(event.globalPos())
