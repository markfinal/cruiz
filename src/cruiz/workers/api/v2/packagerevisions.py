#!/usr/bin/env python3

"""
Get package revisions for a given package reference, recipe revision and package_id
"""

from __future__ import annotations

import datetime
import multiprocessing
import typing

from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(
    queue: multiprocessing.Queue[Message], params: PackageRevisionsParameters
) -> None:
    """
    Equivalent to

    'conan search -r <remote_name> <reference> -rev'

    PackageRevisionsParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        from conan.internal.conan_app import ConanApp
        from conans.model.package_ref import PkgReference

        remote = api.remotes.get(params.remote_name)
        pref = PkgReference.loads(params.reference)
        try:
            app = ConanApp(api)
        except TypeError:
            # older than v2.1.0
            app = ConanApp(api.cache_folder, api.config.global_conf)

        prevs_and_timestamps: typing.List[typing.Dict[str, str]] = []
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
