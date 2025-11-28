#!/usr/bin/env python3

"""Worker implementation for conan remove."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.commandparameters import CommandParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: CommandParameters) -> None:
    """Run 'conan remove [-c] ref'."""
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        from conan.api.model import ListPattern

        assert params.package_reference
        ref_pattern = ListPattern(params.package_reference)
        select_bundle = api.list.select(ref_pattern)

        for ref, _ in select_bundle.refs().items():
            api.remove.recipe(ref)

        queue.put(
            Stdout(
                "Removed packages in the local cache matching pattern "
                f'"{params.package_reference}"'
                " (confirmed)"
                if params.force
                else ""
            )
        )
        queue.put(Success(True))
