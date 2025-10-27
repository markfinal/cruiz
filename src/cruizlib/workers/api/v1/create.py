#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Message, Success
from cruizlib.workers.utils.formatoptions import format_options

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruizlib.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan create'."""
    with worker.ConanWorker(queue, params) as api:
        assert params.recipe_path
        assert params.profile
        args: typing.Dict[str, typing.Union[bool, str, typing.List[str]]] = {
            "profile_names": [params.profile],
        }
        if params.version:
            args["version"] = params.version
        if params.options:
            args["options"] = format_options(params.options)
        if params.user:
            args["user"] = params.user
        if params.channel:
            args["channel"] = params.channel
        if "--update" in params.arguments:
            args["update"] = True

        result = api.create(str(params.recipe_path), **args)

        worker.replace_conan_version_struct_with_string(result)

        queue.put(Success(result))
