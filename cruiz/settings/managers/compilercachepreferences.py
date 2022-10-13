#!/usr/bin/env python3

"""
Settings context manager for compiler cache preferences
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


class CompilerCacheSettings(ComparableCommonSettings):
    """
    Represenation of compiler cache settings
    """

    def __init__(self) -> None:
        self._property_meta = {
            "default": SettingMeta("Default", StringSetting, "None", ScalarValue),
            "ccache_bin_directory": SettingMeta(
                "ccache/BinDir", StringSetting, None, ScalarValue
            ),
            "sccache_bin_directory": SettingMeta(
                "sccache/BinDir", StringSetting, None, ScalarValue
            ),
            "buildcache_bin_directory": SettingMeta(
                "buildcache/BinDir", StringSetting, None, ScalarValue
            ),
        }

    @property
    def default(self) -> StringSetting:
        """
        Get the default compiler cache
        """
        return self._get_value_via_meta()

    @default.setter
    def default(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def ccache_bin_directory(self) -> StringSetting:
        """
        Get the ccache bin directory
        """
        return self._get_value_via_meta()

    @ccache_bin_directory.setter
    def ccache_bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def sccache_bin_directory(self) -> StringSetting:
        """
        Get the sccache bin directory
        """
        return self._get_value_via_meta()

    @sccache_bin_directory.setter
    def sccache_bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def buildcache_bin_directory(self) -> StringSetting:
        """
        Get the buildcache bin directory
        """
        return self._get_value_via_meta()

    @buildcache_bin_directory.setter
    def buildcache_bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)


class CompilerCacheSettingsReader:
    """
    Context manager for reading compiler cache settings from disk
    """

    def __init__(self) -> None:
        self.group = "Thirdparty/CompilerCache"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> CompilerCacheSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = CompilerCacheSettings()
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


class CompilerCacheSettingsWriter(_WriterMixin):
    """
    Utility for writing changed compiler cache settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = CompilerCacheSettingsReader()
