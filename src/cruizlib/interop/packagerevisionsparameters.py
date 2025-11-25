#!/usr/bin/env python3

"""Package revisions parameters."""

import typing

from .commonparameters import CommonParameters


# pylint: disable=too-few-public-methods
class PackageRevisionsParameters(CommonParameters):
    """Representation of all the arguments to get package revisions."""

    def __init__(self, **args: typing.Any) -> None:
        """Initialise a PackageRevisionsParameters."""
        # pylint: disable=import-outside-toplevel
        import cruizlib.workers.api as workers_api

        super().__init__(workers_api.packagerevisions.invoke)
        for k, v in args.items():
            self.__setattr__(k, v)
