#!/usr/bin/env python3

"""
Common parameters
"""

from dataclasses import dataclass, field
import typing


@dataclass
class CommonParameters:
    """
    Common parameters for all commands to run
    """

    worker: typing.Union[
        typing.Callable[[typing.Any, typing.Any], None],
        typing.Callable[[typing.Any, typing.Any, typing.Any], None],
    ]
    added_environment: typing.Dict[str, str] = field(default_factory=dict)
    removed_environment: typing.List[str] = field(default_factory=list)
