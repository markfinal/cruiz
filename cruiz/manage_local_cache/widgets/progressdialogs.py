#!/usr/bin/env python3

"""
Dialog that represent progress of operations
"""

import typing

from qtpy import QtCore, QtWidgets

from cruiz.commands.context import ConanContext


class _ContextProgressDialog(QtWidgets.QProgressDialog):
    """
    Common base class for all progress dialogs.
    """

    def __init__(
        self, context: ConanContext, title: str, parent: QtWidgets.QWidget
    ) -> None:
        super().__init__(title, "Cancel", 0, 0, parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._title = title
        self._context = context
        self.setValue(0)
        self.canceled.connect(self._cancel)

    def _done(self, result: typing.Any, exception: typing.Any) -> None:
        # pylint: disable=unused-argument
        if exception:
            QtWidgets.QMessageBox.critical(
                self, f"{self._title} failed", str(exception)
            )
            return
        self.reset()

    def _cancel(self) -> None:
        self._context.cancel()


class RemoveLocksDialog(_ContextProgressDialog):
    """
    Progress dialog for removing locks from the Conan local cache.
    """

    def __init__(self, context: ConanContext, parent: QtWidgets.QWidget) -> None:
        super().__init__(context, "Removing locks", parent)
        context.remove_local_cache_locks(self._done)


class RemoveAllPackagesDialog(_ContextProgressDialog):
    """
    Progress dialog for removing all packages from the local cache.
    """

    def __init__(self, context: ConanContext, parent: QtWidgets.QWidget) -> None:
        super().__init__(context, "Removing all packages", parent)
        context.remove_all_packages(self._done)
