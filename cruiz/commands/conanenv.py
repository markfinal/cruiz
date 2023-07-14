#!/usr/bin/env python3

"""
Get environment for Conan
"""

import logging
import typing

import cruiz.globals

from cruiz.settings.managers.conanpreferences import ConanSettingsReader
from cruiz.settings.managers.namedlocalcache import NamedLocalCacheSettingsReader


logger = logging.getLogger(__name__)


def get_conan_env(
    cache_name: str,
) -> typing.Tuple[typing.Dict[str, str], typing.List[str]]:
    """
    Get a tuple of
    - a dictionary of environment variables to add
    - a list of environment variable keys to remove
    from the system environment map, in order to invoke Conan commands with
    """
    with NamedLocalCacheSettingsReader(cache_name) as settings:
        home_dir = settings.home_dir.resolve()
        short_home_dir = settings.short_home_dir.resolve()
        added_environment = settings.environment_added.resolve()
        removed_environment = settings.environment_removed.resolve()
    env: typing.Dict[str, str] = {}
    if cruiz.globals.CONAN_MAJOR_VERSION == 1:
        if home_dir:
            env["CONAN_USER_HOME"] = home_dir
        if short_home_dir:
            env["CONAN_USER_HOME_SHORT"] = short_home_dir
    else:
        if home_dir:
            env["CONAN_HOME"] = home_dir
        # short home no longer needed
    env["CONAN_COLOR_DARK"] = "0" if cruiz.globals.is_dark_theme() else "1"
    if cruiz.globals.CONAN_MAJOR_VERSION == 1:
        with ConanSettingsReader() as settings:
            log_level = settings.log_level.resolve()
            env["CONAN_LOGGING_LEVEL"] = log_level
        env["CONAN_NON_INTERACTIVE"] = "1"
    # custom environment variables - this is where cruiz behaviour might vary
    # from Conan on the command line
    env.update(added_environment)
    return (env, removed_environment)
