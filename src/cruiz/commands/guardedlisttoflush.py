#!/usr/bin/env python3

"""
A list, guarded by a mutex, that periodically flushes the joined list
to a QPlainTextEdit
"""

import typing

from qtpy import QtCore, QtWidgets


class GuardedListToFlush(QtCore.QObject):
    """
    Guard a list of strings by a mutex, and flush it to a QPlainTextEdit periodically
    """

    def __init__(self) -> None:
        super().__init__()
        self._widget: typing.Optional[QtWidgets.QPlainTextEdit] = None
        self._list: typing.List[str] = []
        self._guard = QtCore.QMutex()
        self.poll = QtCore.QTimer(self)
        self.poll.timeout.connect(self._flush_list)

    def append(self, message: str) -> None:
        """
        Append a new message to the list.
        """
        # blocking lock
        self._guard.lock()
        self._list.append(message)
        self._guard.unlock()

    def start(self, frequency: int, widget: QtWidgets.QPlainTextEdit) -> None:
        """
        Start flushing the list
        """
        self._widget = widget
        self.poll.start(frequency)

    def stop(self) -> None:
        """
        Stop flushing the list
        """
        self.poll.stop()
        if self._widget:
            # ensure there's no other data left in the buffer
            self._flush_list()

    def _flush_list(self) -> None:
        if not self._list:
            # there may be a thread writing to it, but just wait until the next flush
            return
        if not self._guard.tryLock():
            # give up if writing is happening simultaneously
            return
        combined = "<br>".join(self._list)
        self._list.clear()
        self._guard.unlock()
        assert self._widget
        self._widget.appendHtml(combined)
