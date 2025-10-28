#!/usr/bin/env python3

"""Get package_ids for a given package reference with revision."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruiz.interop.packageidparameters import PackageIdParameters

    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: PackageIdParameters) -> None:
    """
    Equivalent to.

    'conan search -r <remote_name> <reference>'

    PackageIdParameters has dynamic attributes.
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

        # dict of keys of type <class 'conans.model.package_ref.PkgReference'>
        results_dict = app.remote_manager.search_packages(
            remote=remote,
            ref=ref,
        )

        results_list: typing.List[typing.Dict[str, str]] = []
        for ref_pkgid, value in results_dict.items():
            entry = {"id": ref_pkgid.package_id}
            entry.update(value)
            results_list.append(entry)

        queue.put(Success(results_list or None))
