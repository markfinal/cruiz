#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan imports'."""
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
