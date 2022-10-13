#!/usr/bin/env python3

"""
Package id parameters
"""

import typing

from .commonparameters import CommonParameters


class PackageIdParameters(CommonParameters):
    """
    Representation of all the arguments to get package ids
    """

    def __init__(self, **args: typing.Any) -> None:
        import cruiz.workers.packagedetails

        super().__init__(cruiz.workers.packagedetails.invoke)
        for k, v in args.items():
            self.__setattr__(k, v)
