#!/usr/bin/env python3

"""Get source code for the package."""

from __future__ import annotations

import os
import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run 'conan source'."""
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.cwd

        args = {}
        if params.name:
            args["name"] = params.name
        if params.version:
            args["version"] = params.version
        if params.user:
            args["user"] = params.user
        if params.channel:
            args["channel"] = params.channel

        api.local.source(os.fspath(params.recipe_path), **args)
        queue.put(Success(None))
