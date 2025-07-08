#!/usr/bin/env python3

"""Get recipe revisions for the specific package reference."""

from __future__ import annotations

import datetime
import multiprocessing
import typing

from cruizlib.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters


def invoke(
    queue: multiprocessing.Queue[Message], params: RecipeRevisionsParameters
) -> None:
    """
    Equivalent to:.

    'conan search -r <remote_name> <reference> -rev'

    RecipeRevisionsParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        from conan.internal.conan_app import ConanApp

        try:
            from conan.api.model.refs import RecipeReference
        except ImportError:
            # older than v2.12.0
            from conans.model.package_ref import RecipeReference

        assert hasattr(params, "remote_name")
        remote = api.remotes.get(params.remote_name)
        assert hasattr(params, "reference")
        ref = RecipeReference.loads(params.reference)
        try:
            app = ConanApp(api)
        except TypeError:
            # older than v2.1.0
            app = ConanApp(api.cache_folder, api.config.global_conf)

        rrevs_and_timestamps: typing.List[typing.Dict[str, str]] = []
        for new_ref in app.remote_manager.get_recipe_revisions_references(ref, remote):
            rrevs_and_timestamps.append(
                {
                    "revision": new_ref.revision,
                    "time": datetime.datetime.utcfromtimestamp(
                        new_ref.timestamp
                    ).strftime("%Y-%m-%dT%H:%M:%S%Z"),
                }
            )

        queue.put(Success(rrevs_and_timestamps))
