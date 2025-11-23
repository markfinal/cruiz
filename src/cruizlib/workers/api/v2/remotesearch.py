#!/usr/bin/env python3

"""Process requests for searching a remote for package references."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.searchrecipesparameters import SearchRecipesParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(
    queue: MultiProcessingMessageQueueType, params: SearchRecipesParameters
) -> None:
    """
    Equivalent to:.

    'conan search -r <remote_name> [--case-sensitive] <pattern>'

    with optional extra processing when aliases are detected.

    SearchRecipesParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        from conan.api.model import ListPattern

        remote_name = params.remote_name  # type: ignore
        remote = api.remotes.get(remote_name)
        refs: typing.List[typing.Tuple[str, typing.Optional[str]]] = []

        assert hasattr(params, "pattern")

        # api.search removed in v2.20.0
        # https://github.com/conan-io/conan/pull/18726
        # however, api.list.select has been available for a while, so use that

        package_list = api.list.select(
            pattern=ListPattern(params.pattern), remote=remote
        )
        try:
            for first, _ in package_list.items():
                refs.append((str(first), None))
        except AttributeError:
            # in Conan 2.21.0, the items() method was added, but in older,
            # need to use the instance attribute recipes
            for first, _ in package_list.recipes.items():  # pylint: disable=no-member
                refs.append((str(first), None))

        # TODO: alias aware
        # Conan 2 still allows aliases, but not recommended and may be removed in future
        # https://docs.conan.io/2/reference/conanfile/attributes.html#alias

        queue.put(Success(refs or None))
