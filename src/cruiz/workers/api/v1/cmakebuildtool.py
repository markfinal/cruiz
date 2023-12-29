#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success, Stdout, Stderr
from cruiz.workers.utils.worker import Worker
import cruiz.runcommands


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
        if params.added_environment.get("CONAN_CMAKE_GENERATOR") == "Ninja":
            build_cmd.append("-v")
        else:
            params.added_environment["VERBOSE"] = "1"
    if "CONAN_CPU_COUNT" in params.added_environment:
        build_cmd.append(
            f"-j{params.added_environment['CONAN_CPU_COUNT']}"
        )  # suitable for both Make and Ninja
    with Worker(queue, params), cruiz.runcommands.get_popen_for_capture(
        build_cmd,
        cwd=params.cwd,
    ) as process:
        assert process.stdout
        for line in iter(process.stdout.readline, ""):
            queue.put(Stdout(line))
        assert process.stderr
        for line in iter(process.stderr.readline, ""):
            queue.put(Stderr(line))

        queue.put(Success(process.returncode))
