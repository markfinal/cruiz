#!/usr/bin/env python3

"""
Invoke conan create for package creation
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan create'
    """
    with worker.ConanWorker(queue, params) as api:
        import importlib

        # no Python API for create, so reach for the CLI method
        imported_module = importlib.import_module("conan.cli.commands.create")
        # strip the 'verb' from the front of the argument list
        args = params.to_args()[1:]
        imported_module.create.run(api, args)

        queue.put(Success(None))
