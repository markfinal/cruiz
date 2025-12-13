#!/usr/bin/env python3

"""Settings context manager for CMake preferences."""

from __future__ import annotations

import typing

from cruizlib.settings.managers.basesettings import (
    BaseSettings,
    ComparableCommonSettings,
    SettingMeta,
    StringSetting,
)

from .valueclasses import ScalarValue
from .writermixin import _WriterMixin

if typing.TYPE_CHECKING:
    import types


class CMakeSettings(ComparableCommonSettings):
    """Representation of CMake settings."""

    def __init__(self) -> None:
        """Initialise a CMakeSettings."""
        super().__init__()
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
        self,
        exc_type: typing.Optional[type[BaseException]],
        exc_value: typing.Optional[BaseException],
        exc_traceback: types.TracebackType,
    ) -> typing.Any:
        """Exit a context manager with a CMakeSettingsReader."""
        self.settings.endGroup()
        if exc_type is not None:
            # propagate exception
            return False
        return True


class CMakeSettingsWriter(_WriterMixin):
    """Utility class for writing changed CMake settings to disk."""

    def __init__(self) -> None:
        """Initialise a CMakeSettingsWriter."""
        self._reader_for_writer = CMakeSettingsReader()
