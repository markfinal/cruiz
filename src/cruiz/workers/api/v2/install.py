#!/usr/bin/env python3

"""Install dependencies into the local cache."""

from __future__ import annotations

import multiprocessing
import typing

from cruiz.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan install'."""
    with worker.ConanWorker(queue, params) as api:
        import importlib

        # although there is a Python API for install, it works via a dependency
        # graph, so use the CLI interface
        imported_module = importlib.import_module("conan.cli.commands.install")
        # strip the 'verb' from the front of the argument list
        args = params.to_args()[1:]
        imported_module.install.run(api, args)

        queue.put(Success(None))
