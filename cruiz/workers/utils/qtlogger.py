#!/usr/bin/env python3

"""
Qt logger for Conan
"""

from __future__ import annotations

import logging
import multiprocessing
import typing

import conans.util.log

import cruiz.workers.utils.message


class _Singleton(type):
    """
    Base class for all singletons
    """

    _instances: typing.Dict[typing.Any, typing.Any] = {}

    def __call__(cls, *args: typing.Any, **kwargs: typing.Any) -> _Singleton:
        if cls not in cls._instances:
            cls._instances[cls] = super(_Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class QtLogger(logging.Handler, metaclass=_Singleton):
    """
    A logger handler that can be used by Qt to emit signals.
    Signals are delegated to another class that derives from QObject
    This is a singleton.
    """

    def __init__(self) -> None:
        super().__init__()
        formatter = conans.util.log.MultiLineFormatter(
            "%(levelname)-6s:%(filename)-15s[%(lineno)d]: %(message)s [%(asctime)s]"
        )
        self.setFormatter(formatter)
        self._queue: typing.Optional[
            multiprocessing.Queue[cruiz.workers.utils.message.Message]
        ] = None

    def set_queue(
        self, queue: multiprocessing.Queue[cruiz.workers.utils.message.Message]
    ) -> None:
        """
        Set the multiprocessing queue to send messages with.
        """
        self._queue = queue

    def emit(self, record: typing.Any) -> None:
        assert self._queue
        self._queue.put(
            cruiz.workers.utils.message.ConanLogMessage(self.format(record))
        )
