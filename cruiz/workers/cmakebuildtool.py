#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing
import subprocess

from cruiz.interop.commandparameters import CommandParameters
from .utils import worker
from .utils.message import Message, Success, Stdout, Stderr


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    # pylint: disable=too-many-branches
    """
    Run CMake build tool
    """
    assert params.cwd
    # generate build command
    if "CONAN_CMAKE_PROGRAM" in params.added_environment:
        build_cmd = [params.added_environment["CONAN_CMAKE_PROGRAM"]]
    else:
        build_cmd = ["cmake"]
    build_cmd.extend(
        [
            "--build",
            str(params.build_folder) if params.build_folder else ".",
        ]
    )
    # convert "Conan CMake" envvars into CMake envvars
    if "CONAN_MAKE_PROGRAM" in params.added_environment:
        params.added_environment["CMAKE_MAKE_PROGRAM"] = params.added_environment[
            "CONAN_MAKE_PROGRAM"
        ]
    if "CONAN_CMAKE_GENERATOR" in params.added_environment:
        params.added_environment["CMAKE_GENERATOR"] = params.added_environment[
            "CONAN_CMAKE_GENERATOR"
        ]
    if "verbose" in params.arguments:
        if params.added_environment.get("CONAN_CMAKE_GENERATOR", None) == "Ninja":
            build_cmd.append("-v")
        else:
            params.added_environment["VERBOSE"] = "1"
    if "CONAN_CPU_COUNT" in params.added_environment:
        build_cmd.append(
            f"-j{params.added_environment['CONAN_CPU_COUNT']}"
        )  # suitable for both Make and Ninja
    with worker.Worker(queue, params):
        with subprocess.Popen(
            build_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=params.cwd,
        ) as process:
            assert process.stdout
            for line in iter(process.stdout.readline, b""):
                queue.put(Stdout(line.decode("utf-8")))
            assert process.stderr
            for line in iter(process.stderr.readline, b""):
                queue.put(Stderr(line.decode("utf-8")))

            queue.put(Success(process.returncode))
