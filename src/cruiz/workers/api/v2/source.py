#!/usr/bin/env python3

"""
Get source code for the package
"""

from __future__ import annotations

import multiprocessing
import os

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan source'
    """
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
