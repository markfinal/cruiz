"""Test types."""

import queue
import threading
import typing

from cruizlib.interop.message import Message
from cruizlib.multiprocessingmessagequeuetype import (
    MultiProcessingMessageQueueType,
    MultiProcessingStringJoinableQueueType,
)

from tthread import TestableThread  # pylint: disable=wrong-import-order

# Single process
SingleprocessReplyQueueReturnType = typing.Tuple[
    queue.Queue[Message], typing.List[Message], TestableThread
]

# Multi-processing
MultiprocessReplyQueueReturnType = typing.Tuple[
    MultiProcessingMessageQueueType,
    typing.List[Message],
    threading.Thread,
    typing.Any,
]

MultiprocessReplyQueueFixture = typing.Callable[[], MultiprocessReplyQueueReturnType]

# Meta processing
MetaFixture = typing.Tuple[
    MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
]
