#!/usr/bin/env python3

"""
Package binary parameters
"""

import typing

from .commonparameters import CommonParameters


class PackageBinaryParameters(CommonParameters):
    """
    Representation of all the arguments to get package binaries
    """

    def __init__(self, **args: typing.Any) -> None:
        import cruiz.workers.packagebinary

        super().__init__(cruiz.workers.packagebinary.invoke)
        for k, v in args.items():
            self.__setattr__(k, v)
