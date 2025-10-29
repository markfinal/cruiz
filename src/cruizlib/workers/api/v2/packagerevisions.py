#!/usr/bin/env python3

"""Get package revisions for a given package reference, rrev and package_id."""

from __future__ import annotations

import datetime
import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters

    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(
    queue: MultiProcessingMessageQueueType, params: PackageRevisionsParameters
) -> None:
    """
    Equivalent to:.

    'conan search -r <remote_name> <reference> -rev'

    PackageRevisionsParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        # pylint: disable=import-outside-toplevel
        from conan.internal.conan_app import ConanApp

        try:
            from conan.api.model.refs import PkgReference
        except ImportError:
            # older than v2.12.0
            from conans.model.package_ref import PkgReference

        assert hasattr(params, "remote_name")
        remote = api.remotes.get(params.remote_name)
        assert hasattr(params, "reference")
        pref = PkgReference.loads(params.reference)
        try:
            app = ConanApp(api)
        except TypeError:
            # older than v2.1.0
            # pylint: disable=too-many-function-args, no-member
            app = ConanApp(api.cache_folder, api.config.global_conf)

        prevs_and_timestamps: typing.List[typing.Dict[str, str]] = []
        try:
            new_ref = app.remote_manager.get_recipe_revision(pref, remote)
            prevs_and_timestamps.append(
                {
                    "revision": new_ref.revision,
                    "time": datetime.datetime.utcfromtimestamp(
                        new_ref.timestamp
                    ).strftime("%Y-%m-%dT%H:%M:%S%Z"),
                }
            )
        except AttributeError:
            # older than v2.22.0
            # https://github.com/conan-io/conan/commit/aa1f137d546a0c646eaeb29d7637e88c162ead83
            # pylint: disable=no-member
            for new_ref in app.remote_manager.get_package_revisions_references(
                pref, remote
            ):
                prevs_and_timestamps.append(
                    {
                        "revision": new_ref.revision,
                        "time": datetime.datetime.utcfromtimestamp(
                            new_ref.timestamp
                        ).strftime("%Y-%m-%dT%H:%M:%S%Z"),
                    }
                )

        queue.put(Success(prevs_and_timestamps))
