#!/usr/bin/env python3

"""
Get the package binary for a given:
reference, recipe revision, package_id, package revision
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.packagebinaryparameters import PackageBinaryParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(
    queue: multiprocessing.Queue[Message], params: PackageBinaryParameters
) -> None:
    """
    Similar to 'conan download' but the download folder is custom.

    PackageBinaryParameters has dynamic attributes.
    """
    # pylint: disable=import-outside-toplevel, protected-access, no-member
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
        metadata = None

        # TODO: using non-public method
        zipped_files = app.remote_manager._call_remote(
            remote,
            "get_package",
            pref,
            params.where,
            metadata=metadata,
            only_metadata=False,
        )

        queue.put(Success(zipped_files))
