#!/usr/bin/env python3

"""
Get the package binary for a given:.

reference, recipe revision, package_id, package revision
"""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruiz.interop.packagebinaryparameters import PackageBinaryParameters

    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(
    queue: MultiProcessingMessageQueueType, params: PackageBinaryParameters
) -> None:
    """
    Similar to 'conan download' but the download folder is custom.

    PackageBinaryParameters has dynamic attributes.
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
