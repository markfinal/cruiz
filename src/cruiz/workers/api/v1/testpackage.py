#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruiz.workers.utils.formatoptions import format_options

from cruizlib.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan test'."""
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
