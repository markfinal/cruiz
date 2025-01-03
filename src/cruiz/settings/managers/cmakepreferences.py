#!/usr/bin/env python3

"""Settings context manager for CMake preferences."""

import typing

from .basesettings import (
    BaseSettings,
    ComparableCommonSettings,
    SettingMeta,
    StringSetting,
)
from .valueclasses import ScalarValue
from .writermixin import _WriterMixin


class CMakeSettings(ComparableCommonSettings):
    """Representation of CMake settings."""

    def __init__(self) -> None:
        """Initialise a CMakeSettings."""
        self._property_meta = {
            "bin_directory": SettingMeta("BinDir", StringSetting, None, ScalarValue),
        }

    @property
    def bin_directory(self) -> StringSetting:
        """Get the CMake bin directory."""
        return self._get_value_via_meta()

    @bin_directory.setter
    def bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)


class CMakeSettingsReader:
    """Context manager for reading CMake settings from disk."""

    def __init__(self) -> None:
        """Initialise a CMakeSettingsReader."""
        self.group = "Thirdparty/CMake"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> CMakeSettings:
        """Enter a context manager with a CMakeSettingsReader."""
        self.settings.beginGroup(self.group)
        settings = CMakeSettings()
        settings.settings_reader = self
        return settings

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        """Exit a context manager with a CMakeSettingsReader."""
        self.settings.endGroup()
        if exc_type is None:
            pass
        else:
            # propagate exception
            return False


class CMakeSettingsWriter(_WriterMixin):
    """Utility class for writing changed CMake settings to disk."""

    def __init__(self) -> None:
        """Initialise a CMakeSettingsWriter."""
        self._reader_for_writer = CMakeSettingsReader()
