#!/usr/bin/env python3

"""
Utils for worker context managers for Conan v2
"""

import typing

from cruiz.workers.utils.worker import Worker


# pylint: disable=too-few-public-methods
class ConanWorker(Worker):
    """
    Conan specific context manager
    """

    def __enter__(self) -> typing.Any:
        super().__enter__()
        # import here because it can use the environment variables set in the
        # super class
        # pylint: disable=import-outside-toplevel
        from conan.api.conan_api import ConanAPI

        return ConanAPI()
