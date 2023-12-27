#!/usr/bin/env python3

"""
Settings context manager for local cache preferences
"""

import typing

from .basesettings import (
    BaseSettings,
    StringSetting,
    ComparableCommonSettings,
    SettingMeta,
)
from .writermixin import _WriterMixin
from .valueclasses import ScalarValue


# TODO: rename to NewLocalCacheSettings?
class LocalCacheSettings(ComparableCommonSettings):
    """
    Representation of settings for new local caches
    """

    def __init__(self) -> None:
        self._property_meta = {
            "new_configuration_install": SettingMeta(
                "NewConfigInstall", StringSetting, None, ScalarValue
            ),
            "new_configuration_git_branch": SettingMeta(
                "NewConfigGitBranch", StringSetting, None, ScalarValue
            ),
        }

    def presets(self) -> typing.Dict[str, typing.Dict[str, str]]:
        """
        Generate a dictionary of QSettings paths and their values for presets
        """
        group_presets = {}
        new_config = self.new_configuration_install
        if new_config.resolve():
            group_presets["NewConfigInstall"] = new_config.resolve()
        new_config_branch = self.new_configuration_git_branch
        if new_config_branch.resolve():
            group_presets["NewConfigGitBranch"] = new_config_branch.resolve()

        presets = {}
        if group_presets:
            assert self.settings_reader
            presets[self.settings_reader.group] = group_presets
        return presets

    @property
    def new_configuration_install(self) -> StringSetting:
        """
        Get the Conan configuration URL to install for all new local caches
        """
        return self._get_value_via_meta()

    @new_configuration_install.setter
    def new_configuration_install(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def new_configuration_git_branch(self) -> StringSetting:
        """
        Get the Git branch of the Conan configuration to install
        for all new local caches
        """
        return self._get_value_via_meta()

    @new_configuration_git_branch.setter
    def new_configuration_git_branch(self, value: str) -> None:
        self._set_value_via_meta(value)


class LocalCacheSettingsReader:
    """
    Context manager for reading new local cache settings from disk
    """

    def __init__(self) -> None:
        self.group = "LocalCache"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> LocalCacheSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = LocalCacheSettings()
        self._settings_object.settings_reader = self
        return self._settings_object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        self.settings.endGroup()
        self._settings_object.settings_reader = None
        del self._settings_object
        if exc_type is None:
            pass
        else:
            # propagate exception
            return False


class LocalCacheSettingsWriter(_WriterMixin):
    """
    Utility for writing changed new local cache settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = LocalCacheSettingsReader()

    def presets(self, presets: typing.Dict[str, typing.Dict[str, str]]) -> None:
        """
        Take the dictionary of presets and write them to settings.
        There are no checks that these keys are still valid, so importing
        old presets might cause obsolete keys to be saved with no effect.
        """

        if self._reader_for_writer.group in presets:
            with BaseSettings.Group(self._reader_for_writer.group) as settings:
                for key, value in presets[self._reader_for_writer.group].items():
                    settings.setValue(key, value)
