#!/usr/bin/env python3

"""Invoke conan create for package creation."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run 'conan create'."""
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        import importlib

        # no Python API for create, so reach for the CLI method
        imported_module = importlib.import_module("conan.cli.commands.create")
        # strip the 'verb' from the front of the argument list
        args = params.to_args()[1:]
        imported_module.create.run(api, args)

        queue.put(Success(None))
