#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success, Stdout

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan remove [-f] ref'
    """
    with worker.ConanWorker(queue, params) as api:
        assert params.package_reference
        args = {}
        if params.force:
            args["force"] = params.force
        result = api.remove(
            params.package_reference,
            **args,
        )
        queue.put(
            Stdout(
                "Removed packages in the local cache matching pattern "
                f'"{params.package_reference}"'
                " (forced)"
                if params.force
                else ""
            )
        )

        queue.put(Success(result))
