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
    Run 'conan remove [-f] *'
    """
    with worker.ConanWorker(queue, params) as api:
        force = True
        result = api.remove("*", force=force)
        queue.put(
            Stdout(
                "Removed all packages from the local cache" " (forced)" if force else ""
            )
        )

        queue.put(Success(result))
