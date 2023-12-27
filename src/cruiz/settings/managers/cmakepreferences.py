#!/usr/bin/env python3

"""
Settings context manager for CMake preferences
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


class CMakeSettings(ComparableCommonSettings):
    """
    Representation of CMake settings
    """

    def __init__(self) -> None:
        self._property_meta = {
            "bin_directory": SettingMeta("BinDir", StringSetting, None, ScalarValue),
        }

    @property
    def bin_directory(self) -> StringSetting:
        """
        Get the CMake bin directory
        """
        return self._get_value_via_meta()

    @bin_directory.setter
    def bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)


class CMakeSettingsReader:
    """
    Context manager for reading CMake settings from disk
    """

    def __init__(self) -> None:
        self.group = "Thirdparty/CMake"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> CMakeSettings:
        self.settings.beginGroup(self.group)
        settings = CMakeSettings()
        settings.settings_reader = self
        return settings

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        self.settings.endGroup()
        if exc_type is None:
            pass
        else:
            # propagate exception
            return False


class CMakeSettingsWriter(_WriterMixin):
    """
    Utility class for writing changed CMake settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = CMakeSettingsReader()
