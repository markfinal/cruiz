#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success

from . import worker


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
