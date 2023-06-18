#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing
import typing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success
from cruiz.workers.utils.formatoptions import format_options

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan install'
    """
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.cwd
        assert params.profile
        args: typing.Dict[str, typing.Union[bool, str, typing.List[str]]] = {
            "path": str(params.recipe_path),
            "profile_names": [params.profile],
        }
        if params.version:
            args["version"] = params.version
        if params.install_folder:
            args["install_folder"] = str(params.install_folder)
        if params.options:
            args["options"] = format_options(params.options)
        if params.user:
            args["user"] = params.user
        if params.channel:
            args["channel"] = params.channel
        if "--update" in params.arguments:
            args["update"] = True

        result = api.install(**args)
        worker.replace_conan_version_struct_with_string(result)
        queue.put(Success(result))
