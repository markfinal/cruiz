#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing
import typing

from cruiz.interop.commandparameters import CommandParameters
from .utils import worker
from .utils.message import Message, Success


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan export-pkg'
    """
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.cwd
        assert params.name
        args: typing.Dict[str, typing.Union[bool, str]] = {}
        if params.version:
            args["version"] = params.version
        if params.user:
            args["user"] = params.user
        if params.install_folder:
            args["install_folder"] = str(params.install_folder)
        if params.source_folder:
            args["source_folder"] = str(params.source_folder)
        if params.build_folder:
            args["build_folder"] = str(params.build_folder)
        if params.package_folder:
            args["package_folder"] = str(params.package_folder)
        if params.force:
            args["force"] = params.force

        result = api.export_pkg(
            str(params.recipe_path),
            params.name,
            params.channel or None,
            **args,
        )

        worker.replace_conan_version_struct_with_string(result)

        queue.put(Success(result))
