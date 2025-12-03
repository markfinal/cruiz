"""Test types."""

import threading
import typing

from cruizlib.interop.message import Message
from cruizlib.multiprocessingmessagequeuetype import (
    MultiProcessingMessageQueueType,
    MultiProcessingStringJoinableQueueType,
)

MultiprocessReplyQueueReturnType = typing.Tuple[
    MultiProcessingMessageQueueType,
    typing.List[Message],
    threading.Thread,
    typing.Any,
]

MultiprocessReplyQueueFixture = typing.Callable[[], MultiprocessReplyQueueReturnType]


MetaFixture = typing.Tuple[
    MultiProcessingStringJoinableQueueType, MultiProcessingMessageQueueType
]
