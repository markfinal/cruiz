#!/usr/bin/env python3

"""
Get the package binary for a given:.

reference, recipe revision, package_id, package revision
"""

from __future__ import annotations

import typing

from cruiz.interop.message import Message, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing

    from cruiz.interop.packagebinaryparameters import PackageBinaryParameters


def invoke(
    queue: multiprocessing.Queue[Message], params: PackageBinaryParameters
) -> None:
    """
    Similar to 'conan download' but the download folder is custom.

    PackageBinaryParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        from conan.internal.conan_app import ConanApp
        from conans.model.package_ref import PkgReference

        assert hasattr(params, "remote_name")
        remote = api.remotes.get(params.remote_name)
        assert hasattr(params, "reference")
        pref = PkgReference.loads(params.reference)
        try:
            app = ConanApp(api)
        except TypeError:
            # older than v2.1.0
            app = ConanApp(api.cache_folder, api.config.global_conf)
        metadata = None

        assert hasattr(params, "where")
        # pylint: disable=protected-access
        # TODO: call to non-public function
        zipped_files = app.remote_manager._call_remote(
            remote,
            "get_package",
            pref,
            params.where,
            metadata=metadata,
            only_metadata=False,
        )

        queue.put(Success(zipped_files))
