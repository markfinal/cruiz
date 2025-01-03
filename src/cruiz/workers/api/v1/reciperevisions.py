#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import typing
from cruiz.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing
    from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters


def invoke(
    queue: multiprocessing.Queue[Message], params: RecipeRevisionsParameters
) -> None:
    """
    Equivalent to

    'conan search -r <remote_name> <reference> -rev'

    RecipeRevisionsParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        result = api.get_recipe_revisions(
            params.reference,  # type: ignore
            remote_name=params.remote_name,  # type: ignore
        )

        queue.put(Success(result))
