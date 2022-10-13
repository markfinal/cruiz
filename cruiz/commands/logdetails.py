#!/usr/bin/env python3

"""
Logging details
"""

import typing

from qtpy import QtCore, QtWidgets

from .guardedlisttoflush import GuardedListToFlush


class LogDetails(QtCore.QObject):
    """
    Representation of how and where to perform logging during commands
    """

    logging = QtCore.Signal()

    def __init__(
        self,
        output: QtWidgets.QPlainTextEdit,
        error: typing.Optional[QtWidgets.QPlainTextEdit],
        combined: bool,
        batched: bool,
        conan_log: typing.Optional[QtWidgets.QPlainTextEdit],
    ) -> None:
        super().__init__()
        self.output = output
        self.error = output if combined else error
        self._combined = combined
        if combined:
            self._stdout_list = GuardedListToFlush() if batched else None
            self._stderr_list = self._stdout_list
        else:
            self._stdout_list = GuardedListToFlush() if batched else None
            self._stderr_list = GuardedListToFlush() if batched else None
        self._conan_log = conan_log

    def start(self) -> None:
        """
        Start logging
        """
        if self._stdout_list:
            self._stdout_list.start(1000, self.output)
        if self._stderr_list and self._stderr_list != self._stdout_list:
            err_widget = self.output if self._combined else self.error
            assert err_widget
            self._stderr_list.start(1000, err_widget)

    def stop(self) -> None:
        """
        Stop logging
        """
        if self._stdout_list:
            self._stdout_list.stop()
        if self._stderr_list and self._stderr_list != self._stdout_list:
            self._stderr_list.stop()

    def stdout(self, text: str) -> None:
        """
        Append text to stdout
        """
        if self._stdout_list:
            self._stdout_list.append(text)
        else:
            self.output.appendHtml(text)
        self.logging.emit()

    def stderr(self, text: str) -> None:
        """
        Append text to stderr
        """
        if self._stderr_list:
            self._stderr_list.append(text)
        else:
            assert self.error
            self.error.appendHtml(text)
        self.logging.emit()

    def conan_log(self, text: str) -> None:
        """
        Append a Conan log message
        """
        if self._conan_log:
            self._conan_log.appendPlainText(text)
