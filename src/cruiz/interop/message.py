#!/usr/bin/env python3

"""Conan interop message."""

import typing


class Message:
    """Base class of all messages."""


class End(Message):
    """Message to indicate no more messages."""


class Stdout(Message):
    """Message for standard out data."""

    def __init__(self, message: str) -> None:
        """Initialise a Stdout message."""
        super().__init__()
        self._message = message

    def message(self) -> str:
        """Get the message."""
        return self._message


class Stderr(Message):
    """Message for standard error data."""

    def __init__(self, message: str) -> None:
        """Initialise a Stderr message."""
        super().__init__()
        self._message = message

    def message(self) -> str:
        """Get the message."""
        return self._message


class ConanLogMessage(Message):
    """Message for Conan logs."""

    def __init__(self, message: str) -> None:
        """Initialise a ConanLogMessage."""
        super().__init__()
        self._message = message

    def message(self) -> str:
        """Get the message."""
        return self._message


class Success(Message):
    """Message with a result payload for successful completion."""

    def __init__(self, data: typing.Any) -> None:
        """Initialise a Success message."""
        super().__init__()
        self._data = data

    def payload(self) -> typing.Any:
        """Get the successful result."""
        return self._data


class Failure(Message):
    """Message with an exception for a failed command."""

    def __init__(self, exception: Exception) -> None:
        """Initialise a Failure message."""
        super().__init__()
        self._exception = exception

    def exception(self) -> Exception:
        """Get the exception."""
        return self._exception
