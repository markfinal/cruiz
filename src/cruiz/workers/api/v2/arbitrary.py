#!/usr/bin/env python3

"""
Run an arbtitrary Conan command.
It must match one of the Conan verbs though.
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success
import cruiz.runcommands

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run an arbitrary command
    """

    # TODO: is it possible to rewrite this? see the v1 as a model
    """
    with worker.ConanWorker(queue, params) as api:
        from conan.cli.command import ConanCommand

        command = Command(api)
        verb_function = getattr(command, params.verb)
        result = command.run(*params.arguments)
        queue.put(Success(result))
    """
    with worker.ConanWorker(queue, params):
        args = ["conan", params.verb] + params.arguments
        output = cruiz.runcommands.run_get_output(args)
        queue.put(Success(output))
