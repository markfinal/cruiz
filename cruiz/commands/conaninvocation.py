#!/usr/bin/env python3

"""
Representation on the host of an instance of a Conan or Conan-related
command running in a child process
"""

import logging
import multiprocessing
import os
import signal
import sys
import threading
import typing

import psutil

from qtpy import QtCore, QtWidgets

from cruiz.settings.managers.generalpreferences import GeneralSettingsReader
from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.searchrecipesparameters import SearchRecipesParameters
from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters
from cruiz.interop.packageidparameters import PackageIdParameters
from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters
from cruiz.interop.packagebinaryparameters import PackageBinaryParameters

from .messagereplyprocessor import MessageReplyProcessor

from .logdetails import LogDetails


logger = logging.getLogger(__name__)


class ConanInvocation(QtCore.QObject):
    """
    Wrapper around invoking a conan child process
    """

    # pylint: disable=too-many-instance-attributes

    completed = QtCore.Signal(object, Exception)
    finished = QtCore.Signal()
    _begin_processing = QtCore.Signal()

    def __del__(self) -> None:
        logger.debug("-=%d", id(self))

    def __init__(self) -> None:
        logger.debug("+=%d", id(self))
        super().__init__()  # note that parent is None
        self._mp_context = multiprocessing.get_context("spawn")
        self._process_queue = self._mp_context.Queue()
        self._thread = QtCore.QThread()
        self._queue_processor = MessageReplyProcessor(self._process_queue)
        self._queue_processor.moveToThread(self._thread)
        self._begin_processing.connect(self._queue_processor.process)
        self._queue_processor.completed.connect(self.completed)
        # self._thread.finished not guaranteed to be delivered in a
        # qApp quitting scenario
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self.finished)
        self._process: typing.Optional[multiprocessing.context.SpawnProcess] = None
        self._last_command_running: bool = False  # TODO: remove this
        self._cleanup_thread: typing.Optional[threading.Thread] = None

        self._thread.start()
        self._begin_processing.emit()

    def close(self) -> None:
        """
        Tidy up any resources on the context that need closing
        """
        if self._process:
            self._process.join()
            self._process.close()
        self._process = None
        self._queue_processor.stop()
        self._thread.wait()

    def _disconnect_signal(self, result: typing.Any, exception: typing.Any) -> None:
        # pylint: disable=unused-argument
        self._queue_processor.completed.disconnect()
        self._last_command_running = False

    def _critical_failure(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(
            None, "System failure", message  # type: ignore[call-overload]
        )
        sys.exit(1)

    def invoke(
        self,
        parameters: typing.Union[
            CommandParameters,
            SearchRecipesParameters,
            RecipeRevisionsParameters,
            PackageIdParameters,
            PackageRevisionsParameters,
            PackageBinaryParameters,
        ],
        log_details: LogDetails,
        continuation: typing.Optional[typing.Callable[[typing.Any, typing.Any], None]],
    ) -> None:
        """
        Invoke a command, with optional continuation
        """
        assert self._process is None

        if continuation:
            self._queue_processor.completed.connect(continuation)
        self._queue_processor.completed.connect(self._disconnect_signal)

        self._queue_processor.stdout_message.connect(log_details.stdout)
        self._queue_processor.stderr_message.connect(log_details.stderr)
        self._queue_processor.conan_log_message.connect(log_details.conan_log)
        self._queue_processor.critical_failure.connect(self._critical_failure)
        with GeneralSettingsReader() as settings:
            clear_panes = settings.clear_panes.resolve()
        if clear_panes:
            log_details.output.clear()
            if log_details.error:
                log_details.error.clear()

        process = self._mp_context.Process(
            target=parameters.worker,
            args=(self._process_queue, parameters),
            daemon=False,
        )
        process.start()
        logger.debug(
            "cruiz (pid=%i) started child process (pid=%i) for %s",
            os.getpid(),
            process.pid,
            parameters.worker.__module__,
        )
        self._process = process

    def cancel(self) -> None:
        """
        Cancel the current running worker thread.
        """
        if not self._process:
            return
        if not self._process.is_alive():
            return

        pid = self._process.pid
        current_process_psutil = psutil.Process(pid)
        children = current_process_psutil.children(recursive=True)
        self._process.terminate()  # orphans children

        # spawn a daemonic thread to do the child process cleanup
        # doing it in-place was causing shutdown issues on Windows at least
        self._cleanup_thread = threading.Thread(
            target=ConanInvocation._cleanup, args=(pid, children)
        )
        self._cleanup_thread.daemon = True
        self._cleanup_thread.start()

    @staticmethod
    def _cleanup(pid: int, children: typing.List[psutil.Process]) -> None:
        logger.debug("Worker process: %i cancelled", pid)
        logger.debug("Had %i child processes", len(children))
        for i, child in enumerate(children):
            # pylint: disable=broad-except
            try:
                with child.oneshot():
                    logger.debug(
                        "\t%d: %s - %s - %s",
                        i,
                        child.name(),
                        child.cmdline(),
                        child.status(),
                    )
                child.send_signal(signal.SIGTERM)
            except Exception as exception:
                logger.debug("\t%d: %s", i, str(exception))
        psutil.wait_procs(children)
