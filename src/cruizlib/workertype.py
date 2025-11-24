#!/usr/bin/env python3

"""Type annotation for workers."""

import typing

from cruiz.interop.packagebinaryparameters import PackageBinaryParameters
from cruiz.interop.packageidparameters import PackageIdParameters
from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters
from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters

from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.searchrecipesparameters import SearchRecipesParameters
from cruizlib.multiprocessingmessagequeuetype import (
    MultiProcessingMessageQueueType,
    MultiProcessingStringJoinableQueueType,
)

# fmt: off
AllWorkerParameterType = typing.Union[
    CommandParameters,
    SearchRecipesParameters,
    RecipeRevisionsParameters,
    PackageIdParameters,
    PackageRevisionsParameters,
    PackageBinaryParameters
]
# fmt: on


WorkerType = typing.Union[
    # End() worker
    typing.Callable[[MultiProcessingMessageQueueType], None],
    # regular worker
    typing.Callable[[MultiProcessingMessageQueueType, AllWorkerParameterType], None],
    # meta worker
    typing.Callable[
        [
            MultiProcessingStringJoinableQueueType,
            MultiProcessingMessageQueueType,
            AllWorkerParameterType,
        ],
        None,
    ],
]
