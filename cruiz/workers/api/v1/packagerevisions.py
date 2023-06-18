#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

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
        result = api.get_package_revisions(
            params.reference,  # type: ignore
            remote_name=params.remote_name,  # type: ignore
        )

        queue.put(Success(result))
