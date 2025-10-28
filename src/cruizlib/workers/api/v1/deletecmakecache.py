#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing
from pathlib import Path

from cruizlib.interop.message import Stdout, Success
from cruizlib.workers.utils.worker import Worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Delete CMakeCache.txt."""
    with Worker(queue, params):
        assert params.cwd
        cmakecache_file = params.cwd
        if params.build_folder:
            cmakecache_file /= params.build_folder
        cmakecache_file /= "CMakeCache.txt"
        try:
            # Python 3.8+
            Path(cmakecache_file).unlink(missing_ok=True)
        except TypeError:
            Path(cmakecache_file).unlink()
        queue.put(Stdout(f"Deleted {cmakecache_file}"))
        queue.put(Success(None))
