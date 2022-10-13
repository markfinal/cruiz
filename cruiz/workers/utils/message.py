#!/usr/bin/env python3

"""
Conan worker message
"""

import typing


# pylint: disable=too-few-public-methods
class Message:
    """
    Base class of all messages
    """


class End(Message):
    """
    Message to indicate no more messages.
    """


class Stdout(Message):
    """
    Message for standard out data
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def message(self) -> str:
        """
        Get the message
        """
        return self._message


class Stderr(Message):
    """
    Message for standard error data
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def message(self) -> str:
        """
        Get the message
        """
        return self._message


class ConanLogMessage(Message):
    """
    Message for Conan logs
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self._message = message

    def message(self) -> str:
        """
        Get the message
        """
        return self._message


class Success(Message):
    """
    Message with a result payload for successful completion
    """

    def __init__(self, data: typing.Any) -> None:
        super().__init__()
        self._data = data

    def payload(self) -> typing.Any:
        """
        Get the successful result
        """
        return self._data


class Failure(Message):
    """
    Message with an exception for a failed command
    """

    def __init__(self, exception: Exception) -> None:
        super().__init__()
        self._exception = exception

    def exception(self) -> Exception:
        """
        Get the exception
        """
        return self._exception
