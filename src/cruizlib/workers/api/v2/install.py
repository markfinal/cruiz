#!/usr/bin/env python3

"""Install dependencies into the local cache."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run 'conan install'."""
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        import importlib

        # although there is a Python API for install, it works via a dependency
        # graph, so use the CLI interface
        imported_module = importlib.import_module("conan.cli.commands.install")
        # strip the 'verb' from the front of the argument list
        args = params.to_args()[1:]
        imported_module.install.run(api, args)

        queue.put(Success(None))
