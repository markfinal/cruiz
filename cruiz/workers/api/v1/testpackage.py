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
    Run 'conan test'
    """
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.cwd
        assert params.package_reference
        assert params.profile
        args: typing.Dict[str, typing.Union[str, typing.List[str]]] = {
            "profile_names": [params.profile],
        }
        if params.options:
            args["options"] = format_options(params.options)
        if params.test_build_folder:
            args["test_build_folder"] = str(params.test_build_folder)

        result = api.test(
            params.recipe_path,
            params.package_reference,
            **args,
        )

        queue.put(Success(result))
