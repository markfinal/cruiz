#!/usr/bin/env python3

"""Type annotation for multiprocssing Queues on Messages."""

import multiprocessing

from cruizlib.interop.message import Message

# pylint: disable=unsubscriptable-object
MultiProcessingMessageQueueType = multiprocessing.Queue[Message]
