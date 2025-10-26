#!/usr/bin/env python3

"""Worker for runnin conan export-pkg."""

from __future__ import annotations

import multiprocessing
import typing

from cruizlib.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan export-pkg'."""
    with worker.ConanWorker(queue, params) as api:
        import importlib

        # although there is a Python API for export-pkg, it works via a dependency
        # graph, so use the CLI interface
        imported_module = importlib.import_module("conan.cli.commands.export_pkg")
        # strip the 'verb' from the front of the argument list
        args = params.to_args()[1:]
        imported_module.export_pkg.run(api, args)

        queue.put(Success(None))
