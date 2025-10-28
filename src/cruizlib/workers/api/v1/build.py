#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run 'conan build'."""
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
