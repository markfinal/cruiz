#!/usr/bin/env python3

"""
Remove all packages from the local cache
"""

from __future__ import annotations

import typing

from cruiz.interop.message import Message, Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing
    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan remove *'
    """
    with worker.ConanWorker(queue, params) as api:
        from conan.api.model import ListPattern

        ref_pattern = ListPattern("*", rrev="*", prev="*")
        select_bundle = api.list.select(ref_pattern)

        for pkgref in select_bundle.refs().keys():
            api.remove.recipe(pkgref)

        queue.put(Stdout("Removed all packages from the local cache"))
        queue.put(Success(True))
