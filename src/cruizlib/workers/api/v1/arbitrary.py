#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run an arbitrary command."""
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        from conans.client.command import Command

        command = Command(api)
        verb_function = getattr(command, params.verb)
        result = verb_function(params.arguments)
        queue.put(Success(result))
