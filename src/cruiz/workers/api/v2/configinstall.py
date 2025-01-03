#!/usr/bin/env python3

"""Worker for installing Conan local cache configuration."""

from __future__ import annotations

import typing
from io import StringIO

from cruiz.interop.message import Message, Stdout, Success

from . import worker

if typing.TYPE_CHECKING:
    import multiprocessing
    from cruiz.interop.commandparameters import CommandParameters


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """Run 'conan config install'."""
    with worker.ConanWorker(queue, params) as api:
        args = {}
        if "gitBranch" in params.named_arguments:
            args["args"] = f"-b {params.named_arguments['gitBranch']}"
        if "sourceFolder" in params.named_arguments:
            args["source_folder"] = params.named_arguments["sourceFolder"]
        if "targetFolder" in params.named_arguments:
            args["target_folder"] = params.named_arguments["targetFolder"]

        verifySsl = False
        result = api.config.install(
            params.named_arguments["pathOrUrl"], verifySsl, **args
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
