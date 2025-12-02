"""Test types."""

import multiprocessing
import queue
import threading
import typing

from cruizlib.interop.commandparameters import CommandParameters
from cruizlib.interop.message import Message
from cruizlib.interop.packagebinaryparameters import PackageBinaryParameters
from cruizlib.interop.packageidparameters import PackageIdParameters
from cruizlib.interop.packagerevisionsparameters import PackageRevisionsParameters
from cruizlib.interop.reciperevisionsparameters import RecipeRevisionsParameters
from cruizlib.interop.searchrecipesparameters import SearchRecipesParameters
from cruizlib.multiprocessingmessagequeuetype import (
    MultiProcessingMessageQueueType,
    MultiProcessingStringJoinableQueueType,
)

from tthread import TestableThread  # pylint: disable=wrong-import-order

# Single process
SingleprocessReplyQueueReturnType = typing.Tuple[
    queue.Queue[Message],
    typing.List[Message],
    TestableThread,
    None,
]

SingleprocessReplyQueueFixture = typing.Callable[
    [],
    SingleprocessReplyQueueReturnType,
]

# Multi-processing
MultiprocessReplyQueueReturnType = typing.Tuple[
    MultiProcessingMessageQueueType,
    typing.List[Message],
    threading.Thread,
    multiprocessing.context.SpawnContext,
]

MultiprocessReplyQueueFixture = typing.Callable[[], MultiprocessReplyQueueReturnType]

# Run worker
RunWorkerFixture = typing.Callable[
    [
        typing.Any,
        typing.Union[queue.Queue[Message], MultiProcessingMessageQueueType],
        typing.Union[
            CommandParameters,
            PackageBinaryParameters,
            PackageIdParameters,
            PackageRevisionsParameters,
            RecipeRevisionsParameters,
            SearchRecipesParameters,
        ],
        typing.Optional[multiprocessing.context.SpawnContext],
    ],
    None,
]

# Meta processing
MetaFixture = typing.Tuple[
    MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
]
