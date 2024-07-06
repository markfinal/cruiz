#!/usr/bin/env python3

"""
Running commands, a wrapper around subprocess, dealing with Windows console popups
"""

import platform
import subprocess
import typing

CREATION_FLAGS = subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0


def run(*args: typing.Any, **kwargs: typing.Any) -> subprocess.CompletedProcess:  # type: ignore[type-arg]  # noqa: E501
    """
    Run a command, checking for failure.
    """
    kwargs["creationflags"] = CREATION_FLAGS
    kwargs["check"] = True
    return subprocess.run(*args, **kwargs)


def run_get_output(*args: typing.Any, **kwargs: typing.Any) -> str:
    """
    Run a command, to capture stdout.
    Return the output.
    """
    kwargs["creationflags"] = CREATION_FLAGS
    kwargs["check"] = True
    kwargs["capture_output"] = True
    kwargs["encoding"] = "utf-8"
    kwargs["errors"] = "ignore"
    return subprocess.run(*args, **kwargs).stdout


def run_get_combined_output(*args: typing.Any, **kwargs: typing.Any) -> str:
    """
    Run a command, combining and capturing stdout and stderr together
    Return the output.
    """
    kwargs["creationflags"] = CREATION_FLAGS
    kwargs["check"] = True
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.STDOUT
    kwargs["encoding"] = "utf-8"
    kwargs["errors"] = "ignore"
    return subprocess.run(*args, **kwargs).stdout


def get_popen_for_capture(*args: typing.Any, **kwargs: typing.Any) -> subprocess.Popen:  # type: ignore[type-arg]  # noqa: E501
    """
    Get the Popen object, while capturing both stdout and stderr as separate pipes.
    Returns the Popen object.
    """
    kwargs["stdout"] = subprocess.PIPE
    kwargs["stderr"] = subprocess.PIPE
    kwargs["encoding"] = "utf-8"
    kwargs["errors"] = "ignore"
    return subprocess.Popen(*args, **kwargs)
