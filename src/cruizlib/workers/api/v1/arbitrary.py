#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruizlib.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run an arbitrary command."""
    with worker.ConanWorker(queue, params) as api:
        from conans.client.command import Command

        command = Command(api)
        verb_function = getattr(command, params.verb)
        result = verb_function(params.arguments)
        queue.put(Success(result))
