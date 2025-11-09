"""Test exception classes."""

import typing


class FailedMessageTestError(Exception):
    """Exception when a Failure reply is encountered."""

    def __init__(
        self,
        message: str,
        exception_type_name: str,
        exception_traceback: typing.List[str],
    ) -> None:
        """Initialise the exception object."""
        super().__init__(message, exception_type_name, exception_traceback)
        self.exception_type_name = exception_type_name
        self.exception_traceback = exception_traceback


class WatcherThreadTimeoutError(Exception):
    """Exception when the watcher thread has timed out."""
