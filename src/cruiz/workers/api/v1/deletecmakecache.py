#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing
from pathlib import Path

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success, Stdout
from cruiz.workers.utils.worker import Worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Delete CMakeCache.txt
    """
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
