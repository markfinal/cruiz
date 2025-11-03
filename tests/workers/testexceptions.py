"""Test exception classes."""


class FailedMessageTestError(Exception):
    """Exception when a Failure reply is encountered."""


class WatcherThreadTimeoutError(Exception):
    """Exception when the watcher thread has timed out."""
