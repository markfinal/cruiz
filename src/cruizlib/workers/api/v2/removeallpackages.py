#!/usr/bin/env python3

"""Remove all packages from the local cache."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run 'conan remove *'."""
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        from conan.api.model import ListPattern

        ref_pattern = ListPattern("*", rrev="*", prev="*")
        select_bundle = api.list.select(ref_pattern)

        for pkgref in select_bundle.refs():
            api.remove.recipe(pkgref)

        queue.put(Stdout("Removed all packages from the local cache"))
        queue.put(Success(True))
