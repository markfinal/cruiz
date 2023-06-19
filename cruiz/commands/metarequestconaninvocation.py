#!/usr/bin/env python3

"""
Wrapper around a child process, that can process multiple requests for
meta data from a Conan instance
"""

import logging
import multiprocessing
import os
import sys
import typing
import urllib.parse

from qtpy import QtCore

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import (
    Success,
    Failure,
    Stdout,
    Stderr,
    ConanLogMessage,
)
import cruiz.workers.api as workers_api
from cruiz.dumpobjecttypes import dump_object_types

from .conanenv import get_conan_env
from .logdetails import LogDetails


logger = logging.getLogger(__name__)


class MetaRequestConanInvocation(QtCore.QObject):
    """
    Wrapper around request-reply interaction for meta data from a Conan local cache
    Request-replies are synchronous, since it's just metadata
    """

    def __del__(self) -> None:
        logger.debug("-=%d", id(self))

    def __init__(  # noqa: F811
        self,
        parent: QtCore.QObject,
        cache_name: str,
        log_details: LogDetails,
    ) -> None:
        logger.debug("+=%d", id(self))
        super().__init__(parent)
        self._log_details = log_details
        self._mp_context = multiprocessing.get_context("spawn")
        self._request_queue = self._mp_context.JoinableQueue()
        self._reply_queue = self._mp_context.Queue()
        self.active = False
        params = CommandParameters("meta", workers_api.meta.invoke)
        added_environment, removed_environment = get_conan_env(cache_name)
        params.added_environment.update(added_environment)
        params.removed_environment.extend(removed_environment)
        self._invoke_conan_process(params)

    def close(self) -> None:
        """
        Close all resources associated with the invocation
        """
        logger.debug("(%d) closing request queue...", id(self))
        self._request_queue.put("end")
        self._request_queue.join()
        self._request_queue.close()
        self._request_queue.join_thread()
        logger.debug("(%d) closing reply queue...", id(self))
        self._reply_queue.close()
        self._reply_queue.join_thread()
        logger.debug("(%d) joining process...", id(self))
        self._process.join()
        self._process.close()

    def _invoke_conan_process(self, params: CommandParameters) -> None:
        process = self._mp_context.Process(
            target=params.worker,
            args=(self._request_queue, self._reply_queue, params),
            daemon=False,
        )
        process.start()
        logger.debug(
            "cruiz (pid=%i) started child process (pid=%i) for %s",
            os.getpid(),
            process.pid,
            params.worker.__module__,
        )
        self._process = process

    @staticmethod
    def __check_for_conan_leakage(entry: typing.Any = None) -> None:
        if "conans" not in sys.modules:
            return
        if entry:
            logger.critical("Conan has leaked into message queue object dump:")
            dump_object_types(entry, loglevel="CRITICAL")
        logger.critical("Conan has leaked into cruiz")
        sys.exit(1)

    def request_data(
        self,
        request: typing.Any,
        params: typing.Optional[typing.Dict[str, typing.Any]] = None,
    ) -> typing.Tuple[typing.Any, typing.Optional[Exception]]:
        """
        Request a named metadata, and synchronously wait for a reply.
        Reply is a tuple, with result and exception.
        """
        meta_request = (
            f"{request}?{urllib.parse.urlencode(params, doseq=True)}"
            if params
            else request
        )
        logger.debug("* Requesting %s", meta_request)
        self._request_queue.put(meta_request)
        self.active = True
        logger.debug("* Requested %s waiting for reply", meta_request)
        # the requested task is done when there is a success or a failure
        self._request_queue.join()
        response: typing.Union[
            Success,
            Failure,
            None,
        ] = None
        while True:
            MetaRequestConanInvocation.__check_for_conan_leakage(None)
            reply = self._reply_queue.get()
            MetaRequestConanInvocation.__check_for_conan_leakage(reply)
            if isinstance(reply, Stdout):
                logger.debug("* Got stdout message: '%s", reply.message())
                self._log_details.stdout(reply.message())
            elif isinstance(reply, Stderr):
                logger.debug("* Got stderr message: '%s", reply.message())
                self._log_details.stderr(reply.message())
            elif isinstance(reply, ConanLogMessage):
                logger.debug("* Got Conan log message: '%s", reply.message())
                self._log_details.conan_log(reply.message())
            elif isinstance(reply, Success):
                logger.debug("* Requested %s got reply '%s'", meta_request, reply)
                response = reply
                break
            elif isinstance(reply, Failure):
                logger.debug("* Got failure message: '%s'", str(reply.exception()))
                response = reply
                break
        assert self._reply_queue.empty()
        self.active = False
        if response is not None:
            if isinstance(reply, Success):
                return (response.payload(), None)  # type: ignore
            if isinstance(reply, Failure):
                return (None, response.exception())  # type: ignore
        raise RuntimeError("No success message")
