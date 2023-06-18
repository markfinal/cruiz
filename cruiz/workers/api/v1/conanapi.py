#!/usr/bin/env python3

"""
Create an instance of the Conan API object
"""

from __future__ import annotations

import multiprocessing
import os
import pathlib
import typing

# must be performed before conan is imported
from .monkeypatch import _do_monkey_patching

_do_monkey_patching()

# pylint: disable=wrong-import-order,wrong-import-position
from conans.client import conan_api, output, runner  # noqa: E402
from conans.paths import get_conan_user_home  # noqa: E402

import cruiz.workers.utils.qtlogger  # noqa: E402
from cruiz.workers.utils.stream import QueuedStreamSix  # noqa: E402
from cruiz.interop.commandparameters import CommandParameters  # noqa: E402
from cruiz.interop.commonparameters import CommonParameters  # noqa: E402
from cruiz.interop.message import Message, Stdout, Stderr  # noqa: E402


def instance(
    queue: multiprocessing.Queue[Message],
    params: typing.Union[CommandParameters, CommonParameters],
) -> conan_api.ConanAPIV1:
    """
    Get a new instance of the Conan API object
    """
    # pylint: disable=no-member
    cruiz.workers.utils.qtlogger.QtLogger().set_queue(queue)
    stdout = QueuedStreamSix(queue, Stdout)
    stderr = QueuedStreamSix(queue, Stderr)
    newoutputter = output.ConanOutput(stream=stdout, stream_err=stderr, color=True)
    if isinstance(params, CommandParameters):
        home_dir = pathlib.Path(
            params.added_environment.get("CONAN_USER_HOME", get_conan_user_home())
        )
        local_cache_dir = home_dir / ".conan"
        cache = conan_api.ClientCache(local_cache_dir, stdout)
        print_commands_to_output = cache.config.print_commands_to_output
        if params.cwd:
            # TODO: this has some broken assumptions about pure paths
            if isinstance(params.cwd, pathlib.PurePosixPath):
                path = pathlib.Path(params.cwd)
                path.mkdir(parents=True, exist_ok=True)
            else:
                params.cwd.mkdir(parents=True, exist_ok=True)
            os.chdir(params.cwd)
    elif isinstance(params, CommonParameters):
        home_dir = pathlib.Path(
            params.added_environment.get("CONAN_USER_HOME", get_conan_user_home())
        )
        local_cache_dir = home_dir / ".conan"
        cache = conan_api.ClientCache(local_cache_dir, stdout)
        print_commands_to_output = False

    newrunner = runner.ConanRunner(
        print_commands_to_output=print_commands_to_output, output=newoutputter
    )

    try:
        api = conan_api.ConanAPIV1(output=newoutputter, runner=newrunner)
        api.create_app()
    except TypeError:
        api = _create_old_conan_api(newoutputter, newrunner)
        api.invalidate_caches()
    return api


def _create_old_conan_api(out: typing.Any, run: typing.Any) -> typing.Any:
    # This function is mostly copied from Conan 1.17.x Factory methood for ConanAPIV1,
    # but with edits for cruiz
    # pylint: disable=logging-not-lazy,import-outside-toplevel,too-many-locals,
    # pylint: disable=unexpected-keyword-arg,no-member,no-value-for-parameter,
    # pylint: disable=too-many-function-args
    import sys
    from conans.client.userio import UserIO
    from conans.client.migrations import ClientMigrator
    from conans.client.hook_manager import HookManager
    from conans.client.cache.cache import ClientCache
    from conans.client.rest.rest_client import RestApiClient
    from conans.client.store.localdb import LocalDB
    from conans.model.version import Version
    from conans import __version__ as client_version
    from conans.util.log import configure_logger
    from conans.client.rest.conan_requester import ConanRequester
    from conans.client.rest.auth_manager import ConanApiAuthManager
    from conans.client.remote_manager import RemoteManager
    from conans.tools import set_global_instances
    from conans.client.conan_api import ConanAPIV1
    from conans.paths import get_conan_user_home
    import conans

    user_io = UserIO(out=out)

    user_home = pathlib.Path(get_conan_user_home())
    base_folder = user_home / ".conan"

    cache = ClientCache(base_folder, out)
    # Migration system
    migrator = ClientMigrator(cache, Version(client_version), out)
    migrator.migrate()

    if base_folder:
        sys.path.append(os.fspath(base_folder / "python"))

    config = cache.config
    # Adjust CONAN_LOGGING_LEVEL with the env readed
    conans.util.log.logger = configure_logger(config.logging_level, config.logging_file)
    conans.util.log.logger.debug("INIT: Using config '%s'", cache.conan_conf_path)

    hook_manager = HookManager(cache.hooks_path, config.hooks, user_io.out)
    # Wraps an http_requester to inject proxies, certs, etc
    requester = ConanRequester(config)
    # To handle remote connections
    put_headers = cache.read_put_headers()
    rest_api_client = RestApiClient(
        user_io.out,
        requester,
        revisions_enabled=config.revisions_enabled,
        put_headers=put_headers,
    )
    # To store user and token
    localdb = LocalDB.create(cache.localdb)
    # Wraps RestApiClient to add authentication support (same interface)
    auth_manager = ConanApiAuthManager(rest_api_client, user_io, localdb)
    # Handle remote connections
    remote_manager = RemoteManager(cache, auth_manager, user_io.out, hook_manager)

    # Adjust global tool variables
    set_global_instances(out, requester)

    # Settings preprocessor
    interactive = False

    return ConanAPIV1(
        cache,
        user_io,
        run,
        remote_manager,
        hook_manager,
        requester,
        interactive=interactive,
    )
