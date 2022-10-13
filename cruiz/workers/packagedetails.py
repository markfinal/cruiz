#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.packageidparameters import PackageIdParameters

from .utils import worker
from .utils.message import Message, Success


def invoke(queue: multiprocessing.Queue[Message], params: PackageIdParameters) -> None:
    """
    Equivalent to

    'conan search -r <remote_name> <reference>'

    PackageIdParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        result = api.search_packages(
            params.reference,  # type: ignore
            remote_name=params.remote_name,  # type: ignore
        )
        results_list = result["results"][0]["items"][0]["packages"]

        queue.put(Success(results_list or None))
