#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

from io import StringIO
import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.message import Message, Success, Stdout

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan config install'
    """
    with worker.ConanWorker(queue, params) as api:
        args = {}
        if "gitBranch" in params.named_arguments:
            args["args"] = f"-b {params.named_arguments['gitBranch']}"
        if "sourceFolder" in params.named_arguments:
            args["source_folder"] = params.named_arguments["sourceFolder"]
        if "targetFolder" in params.named_arguments:
            args["target_folder"] = params.named_arguments["targetFolder"]

        result = api.config_install(
            params.named_arguments["pathOrUrl"],
            False,  # TODO do we want verify SSL to be false?
            **args,
        )
        message = StringIO()
        message.write(
            "Configuration installed from " f'{params.named_arguments["pathOrUrl"]}'
        )
        if "args" in args:
            message.write(f" with arguments {args['args']} ")
        if "source_folder" in args:
            message.write(f" from source folder {args['source_folder']} ")
        if "target_folder" in args:
            message.write(f" to target folder {args['target_folder']} ")
        queue.put(Stdout(message.getvalue()))
        queue.put(Success(result))
