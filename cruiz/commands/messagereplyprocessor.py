#!/usr/bin/env python3

"""
Worker class that is run on a background thread, processing replies
from child processes and converting to signals.
"""

from __future__ import annotations

import logging
import multiprocessing
import sys
import typing

from qtpy import QtCore

from cruiz.dumpobjecttypes import dump_object_types

import cruiz.workers.api as workers_api
from cruiz.interop.message import (
    Message,
    End,
    Stdout,
    Stderr,
    Success,
    Failure,
    ConanLogMessage,
)

logger = logging.getLogger(__name__)


class MessageReplyProcessor(QtCore.QObject):
    """
    Process replies across a multiprocessing Queue in a background thread.
    Emit signals for recognised messages, since you cannot add to UI in a
    background thread.
    """

    completed = QtCore.Signal(object, Exception)
    stdout_message = QtCore.Signal(str)
    stderr_message = QtCore.Signal(str)
    conan_log_message = QtCore.Signal(str)
    critical_failure = QtCore.Signal(str)

    def __del__(self) -> None:
        logger.debug("-=%d", id(self))

    def __init__(
        self,
        queue: multiprocessing.Queue[Message],
    ):
        logger.debug("+=%d", id(self))
        super().__init__()
        self._mp_context = multiprocessing.get_context("spawn")
        self._queue = queue

    def stop(self) -> None:
        """
        Stop the background thread.
        """
        # start a process to shut down the thread
        shutdown_process = self._mp_context.Process(
            target=workers_api.endmessagethread.invoke, args=(self._queue,)
        )
        shutdown_process.start()
        shutdown_process.join()
        shutdown_process.close()

    def __check_for_conan_leakage(self, entry: typing.Any = None) -> bool:
        if "conans" not in sys.modules:
            return True
        if entry:
            logger.critical("Conan has leaked into message queue object dump:")
            dump_object_types(entry, loglevel="CRITICAL")
            raise AssertionError("Conan has leaked into cruiz")
        self.critical_failure.emit("Conan has leaked into cruiz")
        return False

    # pylint: disable=too-many-branches
    def process(self) -> None:
        """
        Process messages received from a child process.
        """
        try:
            # pylint: disable=import-error,import-outside-toplevel
            # make any debugger aware of this thread
            import pydevd

            pydevd.settrace(suspend=False)
        except ModuleNotFoundError:
            pass
        while True:
            logger.debug("(%d) wait for queue entry...", id(self))
            try:
                if not self.__check_for_conan_leakage(None):
                    break
                entry = self._queue.get()
                if not self.__check_for_conan_leakage(entry):
                    break
                if isinstance(entry, End):
                    break
                if isinstance(entry, Stdout):
                    self.stdout_message.emit(entry.message())
                elif isinstance(entry, Stderr):
                    self.stderr_message.emit(entry.message())
                elif isinstance(entry, ConanLogMessage):
                    self.conan_log_message.emit(entry.message())
                elif isinstance(entry, Success):
                    self.completed.emit(entry.payload(), None)
                elif isinstance(entry, Failure):
                    # TODO: temporary, at least always record the exception
                    # in the error log
                    self.stderr_message.emit(str(entry.exception()))
                    self.completed.emit(None, entry.exception())
                else:
                    logger.error("Unknown message type: '%s'", entry)
            except EOFError as exception:
                logger.debug(
                    "(%d) queue failed because %s",
                    id(self),
                    str(exception),
                )
        logger.debug("(%d) closing queue...", id(self))
        self._queue.close()
        self._queue.join_thread()
        logger.debug("(%d) closed queue", id(self))
        QtCore.QThread.currentThread().quit()
