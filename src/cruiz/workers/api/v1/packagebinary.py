#!/usr/bin/env python3

"""Child process commands."""

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
    from conans.model.ref import PackageReference

    with worker.ConanWorker(queue, params) as api:
        try:
            # Conan 1.18+
            remote_manager = api.app.remote_manager
        except AttributeError:
            # pylint: disable=protected-access
            remote_manager = api._remote_manager

        remote_name = params.remote_name  # type: ignore
        pkgref = params.reference  # type: ignore
        where = params.where  # type: ignore

        try:
            # Conan 1.19+
            remotes = api.app.load_remotes(remote_name=remote_name)
        except AttributeError:
            try:
                # Conan 1.18.x
                remotes = api.app.cache.registry.load_remotes()
            except AttributeError:
                # pylint: disable=protected-access
                remotes = api._cache.registry.load_remotes()
        remote = remotes.get_remote(remote_name)
        pref_str = pkgref
        pref = PackageReference.loads(pref_str)
        # pylint: disable=protected-access
        # from RemoteManager.get_package, intentionally calling non-public functions
        snapshot = remote_manager._call_remote(remote, "get_package_snapshot", pref)
        remote_manager._call_remote(remote, "get_package", pref, where)

        queue.put(Success(snapshot))
