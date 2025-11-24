#!/usr/bin/env python3

"""Get recipe revisions for the specific package reference."""

from __future__ import annotations

import datetime
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
    Equivalent to:.

    'conan search -r <remote_name> <reference> -rev'

    RecipeRevisionsParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
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
            # pylint: disable=too-many-function-args, no-member
            app = ConanApp(api.cache_folder, api.config.global_conf)

        rrevs_and_timestamps: typing.List[typing.Dict[str, str]] = []
        try:
            for new_ref in app.remote_manager.get_recipe_revisions(ref, remote):
                rrevs_and_timestamps.append(
                    {
                        "revision": new_ref.revision,
                        "time": datetime.datetime.utcfromtimestamp(
                            new_ref.timestamp
                        ).strftime("%Y-%m-%dT%H:%M:%S%Z"),
                    }
                )
        except AttributeError:
            # changed in v2.22.0
            # https://github.com/conan-io/conan/commit/aa1f137d546a0c646eaeb29d7637e88c162ead83
            # pylint: disable=no-member
            for new_ref in app.remote_manager.get_recipe_revisions_references(
                ref, remote
            ):
                rrevs_and_timestamps.append(
                    {
                        "revision": new_ref.revision,
                        "time": datetime.datetime.utcfromtimestamp(
                            new_ref.timestamp
                        ).strftime("%Y-%m-%dT%H:%M:%S%Z"),
                    }
                )

        queue.put(Success(rrevs_and_timestamps))
