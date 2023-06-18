#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

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
        if params.install_folder:
            args["info_folder"] = params.install_folder
        if params.source_folder:
            args["source_folder"] = params.source_folder

        result = api.source(str(params.recipe_path), **args)
        queue.put(Success(result))
