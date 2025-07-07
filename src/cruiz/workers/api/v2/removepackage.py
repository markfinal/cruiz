#!/usr/bin/env python3

"""Worker implementation for conan remove."""

from __future__ import annotations

import typing

from cruiz.interop.message import Message, Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan remove [-c] ref'."""
    with worker.ConanWorker(queue, params) as api:
        from conan.api.model import ListPattern

        assert params.package_reference
        ref_pattern = ListPattern(params.package_reference)
        select_bundle = api.list.select(ref_pattern)

        for ref, _ in select_bundle.refs():
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
