#!/usr/bin/env python3

"""Child process commands."""

from __future__ import annotations

import typing

from cruizlib.interop.message import Success

from . import worker

if typing.TYPE_CHECKING:
    from cruizlib.interop.packageidparameters import PackageIdParameters
    from cruizlib.multiprocessingmessagequeuetype import MultiProcessingMessageQueueType


def invoke(queue: MultiProcessingMessageQueueType, params: PackageIdParameters) -> None:
    """
    Equivalent to.

    'conan search -r <remote_name> <reference>'

    PackageIdParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        assert hasattr(params, "reference")
        assert hasattr(params, "remote_name")

        result = api.search_packages(
            params.reference,
            remote_name=params.remote_name,
        )
        results_list = result["results"][0]["items"][0]["packages"]

        # pylint: disable=import-outside-toplevel
        import conans

        for entry in results_list:
            if "options" in entry:
                new_options = {}
                for option_key, option_value in entry["options"].items():
                    assert isinstance(
                        option_value, conans.model.options.PackageOptionValue
                    )
                    new_options[option_key] = str(option_value)
                entry["options"] = new_options

        queue.put(Success(results_list or None))
