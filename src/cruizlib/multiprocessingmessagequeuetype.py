#!/usr/bin/env python3

"""Type annotation for multiprocssing Queues on Messages."""

import multiprocessing
import multiprocessing.queues

from cruizlib.interop.message import Message

# multiprocessing.Queue is a function rather than a class, so it does not satisfy
# the usual static type rules
# multiprocessing.queues is undocumented in more recent Pythons
# see https://github.com/python/cpython/issues/99509#issuecomment-1742069772
# unfortunately canot do this while older Pythons (at least 3.10) are being tested
try:
    MultiProcessingMessageQueueType = multiprocessing.queues.Queue[Message]
    MultiProcessingStringJoinableQueueType = multiprocessing.queues.JoinableQueue[str]
except TypeError:
    # pylint: disable=unsubscriptable-object
    MultiProcessingMessageQueueType = multiprocessing.Queue[Message]
    MultiProcessingStringJoinableQueueType = multiprocessing.JoinableQueue[str]
