#!/usr/bin/env python3

"""
Build the source code of the package
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan build'
    """
    with worker.ConanWorker(queue, params) as api:
        import importlib

        # although there is a Python API for build, the setup was complex, as it
        # expected a fully configured conanfile object (e.g. for paths, layouts etc)
        # so reach for the CLI method
        imported_module = importlib.import_module("conan.cli.commands.build")
        # strip the 'verb' from the front of the argument list
        args = params.to_args()[1:]
        imported_module.build.run(api, args)

        queue.put(Success(None))
