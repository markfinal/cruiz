#!/usr/bin/env python3

"""Package id parameters."""

import typing

from .commonparameters import CommonParameters


# pylint: disable=too-few-public-methods
class PackageIdParameters(CommonParameters):
    """Representation of all the arguments to get package ids."""

    def __init__(self, **args: typing.Any) -> None:
        """Initialise a PackageIdParameters."""
        # pylint: disable=import-outside-toplevel
        import cruizlib.workers.api as workers_api

        super().__init__(workers_api.packagedetails.invoke)
        for k, v in args.items():
            self.__setattr__(k, v)
