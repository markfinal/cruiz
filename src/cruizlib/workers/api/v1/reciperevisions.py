#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.reciperevisionsparameters import RecipeRevisionsParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(
    queue: MultiProcessingMessageQueueType, params: RecipeRevisionsParameters
) -> None:
    """
    Equivalent to.

    'conan search -r <remote_name> <reference> -rev'

    RecipeRevisionsParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        assert hasattr(params, "reference")
        assert hasattr(params, "remote_name")

        result = api.get_recipe_revisions(
            params.reference,
            remote_name=params.remote_name,
        )

        queue.put(Success(result))
