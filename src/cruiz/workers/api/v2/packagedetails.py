#!/usr/bin/env python3

"""
Get package_ids for a given package reference with revision
"""

from __future__ import annotations

import multiprocessing
import typing

from cruiz.interop.packageidparameters import PackageIdParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: PackageIdParameters) -> None:
    """
    Equivalent to

    'conan search -r <remote_name> <reference>'

    PackageIdParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        from conan.internal.conan_app import ConanApp
        from conans.model.recipe_ref import RecipeReference

        remote = api.remotes.get(params.remote_name)
        ref = RecipeReference.loads(params.reference)
        try:
            app = ConanApp(api)
        except TypeError:
            # older than v2.1.0
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
