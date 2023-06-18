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
    Run 'conan imports'
    """
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.cwd
        args = {
            "path": str(params.recipe_path),
        }
        if params.install_folder:
            args["info_folder"] = str(params.install_folder)
        if params.imports_folder:
            args["dest"] = str(params.imports_folder)
        result = api.imports(**args)

        queue.put(Success(result))
