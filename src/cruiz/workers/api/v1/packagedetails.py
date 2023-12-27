#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

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
        result = api.search_packages(
            params.reference,  # type: ignore
            remote_name=params.remote_name,  # type: ignore
        )
        results_list = result["results"][0]["items"][0]["packages"]

        import conans

        for entry in results_list:
            if "options" in entry:
                new_options = {}
                for option_key, option_value in entry["options"].items():
                    if isinstance(
                        option_value, conans.model.options.PackageOptionValue
                    ):
                        new_options[option_key] = str(option_value)
                    else:
                        new_options[option_key] = option_value
                entry["options"] = new_options

        queue.put(Success(results_list or None))
