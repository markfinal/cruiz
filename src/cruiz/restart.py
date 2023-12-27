#!/usr/bin/env python3

"""
Restart the whole application
"""

from qtpy import QtCore


def restart_cruiz() -> None:
    """
    Quit the application and restart it.
    """
    qApp.quit()  # type: ignore[name-defined] # noqa: F821
    QtCore.QProcess.startDetached(
        qApp.arguments()[0], qApp.arguments()  # type: ignore[name-defined] # noqa: F821
    )
