#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import contextlib
import multiprocessing
import os
import typing

from cruiz.interop.commandparameters import CommandParameters

from .utils import worker
from .utils.message import Message, Success


@contextlib.contextmanager
def use_package_cwd(cwd: str) -> typing.Iterator[None]:
    """
    Context manager to change directory and back again when finished.
    """
    curdir = os.getcwd()
    try:
        os.chdir(cwd)
        yield
    finally:
        os.chdir(curdir)


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run an arbitrary command
    """
    with worker.ConanWorker(queue, params) as api:
        from conans.client.command import Command

        command = Command(api)
        verb_function = getattr(command, params.verb)
        result = verb_function(params.arguments)
        queue.put(Success(result))
