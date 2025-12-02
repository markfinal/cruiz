"""Ability to test a thread."""

import threading
import typing


class TestableThread(threading.Thread):
    """
    Wrapper around `threading.Thread` that propagates exceptions.

    REF: https://gist.github.com/sbrugman/59b3535ebcd5aa0e2598293cfa58b6ab
    """

    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        """Subclassed from threading.Thread."""
        super().__init__(*args, **kwargs)
        self.exc: typing.Optional[BaseException] = None

    def run(self) -> None:
        """Subclassed from threading.Thread."""
        try:
            super().run()
        # pylint: disable=broad-exception-caught
        except BaseException as e:  # noqa: B036
            self.exc = e

    def join(self, timeout: typing.Optional[float] = None) -> None:
        """Subclassed from threading.Thread."""
        super().join(timeout)
        if self.exc:
            raise self.exc
