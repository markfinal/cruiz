#!/usr/bin/env python3

"""Process requests for searching a remote for package references."""

from __future__ import annotations

import typing

from cruiz.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing
    from cruiz.interop.searchrecipesparameters import SearchRecipesParameters


def invoke(
    queue: multiprocessing.Queue[Message], params: SearchRecipesParameters
) -> None:
    """
    Equivalent to:.

    'conan search -r <remote_name> [--case-sensitive] <pattern>'

    with optional extra processing when aliases are detected.

    SearchRecipesParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        remote_name = params.remote_name  # type: ignore
        remote = api.remotes.get(remote_name)
        refs: typing.List[typing.Tuple[str, typing.Optional[str]]] = []

        assert hasattr(params, "pattern")
        for ref in api.search.recipes(query=params.pattern, remote=remote):
            # returns a list of conans.model.recipe_ref.RecipeReference
            refs.append((str(ref), None))

        # TODO: alias aware

        queue.put(Success(refs or None))
