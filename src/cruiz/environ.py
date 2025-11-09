#!/usr/bin/env python3

"""Utility to save and restore the os.environ temporarily using a with statement."""

import os
import types
import typing


class EnvironSaver:
    """Use a 'with' statement to limit the scope of these changes."""

    def __init__(self) -> None:
        """Initialise an EnvironSaver."""
        self._saved: typing.Optional[typing.Dict[str, str]] = None

    def __enter__(self) -> None:
        """Enter a context manager with an EnvironSaver."""
        self._saved = os.environ.copy()

    def __exit__(
        self,
        exc_type: typing.Optional[type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: types.TracebackType,
    ) -> None:
        """Exit a context manager with an EnvironSaver."""
        self.restore()

    def restore(self) -> None:
        """Restore os.environ to that saved."""
        os.environ.clear()
        # TODO: want to use this next statement, but mypy has an issue with it
        # os.environ.update(self._saved)
        assert self._saved
        for key, value in self._saved.items():
            os.environ[key] = value
