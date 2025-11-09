#!/usr/bin/env python3

# pylint: disable=too-few-public-methods

"""Conan interop message."""

from __future__ import annotations

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

    @property
    def message(self) -> str:
        """Get the message."""
        return self._message


class Stderr(Message):
    """Message for standard error data."""

    def __init__(self, message: str) -> None:
        """Initialise a Stderr message."""
        super().__init__()
        self._message = message

    @property
    def message(self) -> str:
        """Get the message."""
        return self._message


class ConanLogMessage(Message):
    """Message for Conan logs."""

    def __init__(self, message: str) -> None:
        """Initialise a ConanLogMessage."""
        super().__init__()
        self._message = message

    @property
    def message(self) -> str:
        """Get the message."""
        return self._message


class Success(Message):
    """Message with a result payload for successful completion."""

    def __init__(self, data: typing.Any) -> None:
        """Initialise a Success message."""
        super().__init__()
        self._data = data

    @property
    def payload(self) -> typing.Any:
        """Get the successful result."""
        return self._data


class Failure(Message):
    """Message with optional exception details for a failed command."""

    def __init__(
        self, message: str, exception_type_name: str, traceback: typing.List[str]
    ) -> None:
        """Initialise a Failure message."""
        super().__init__()
        self._message = message
        self._exception_type_name = exception_type_name
        self._traceback = traceback
        self._html_message: typing.Optional[str] = None

    @property
    def message(self) -> str:
        """Get the message."""
        return self._message

    @property
    def exception_type_name(self) -> str:
        """Get the name of the exception type that raised the failure."""
        return self._exception_type_name

    @property
    def exception_traceback(self) -> typing.List[str]:
        """Get the traceback of the exception that raised the failure."""
        return self._traceback

    @property
    def html(self) -> typing.Optional[str]:
        """Get the HTML exception message."""
        return self._html_message

    @html.setter
    def html(self, html_message: str) -> None:
        """Set the HTML exception message."""
        self._html_message = html_message
