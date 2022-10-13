#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from .utils import worker
from .utils.message import Message, Success


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan build'
    """
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.cwd
        args = {}
        if params.install_folder:
            args["install_folder"] = params.install_folder
        if params.source_folder:
            args["source_folder"] = params.source_folder
        if params.build_folder:
            args["build_folder"] = params.build_folder
        if params.package_folder:
            args["package_folder"] = params.package_folder

        result = api.build(str(params.recipe_path), **args)
        queue.put(Success(result))
