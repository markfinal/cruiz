#!/usr/bin/env python3

"""Package binary parameters."""

import typing

from cruizlib.interop.commonparameters import CommonParameters


# pylint: disable=too-few-public-methods
class PackageBinaryParameters(CommonParameters):
    """Representation of all the arguments to get package binaries."""

    def __init__(self, **args: typing.Any) -> None:
        """Initialise a PackageBinaryParameters."""
        # pylint: disable=import-outside-toplevel
        import cruizlib.workers.api as workers_api

        super().__init__(workers_api.packagebinary.invoke)
        for k, v in args.items():
            self.__setattr__(k, v)
