#!/usr/bin/env python3

"""Settings context manager for Ninja preferences."""

import typing

from .basesettings import (
    BaseSettings,
    ComparableCommonSettings,
    SettingMeta,
    StringSetting,
)
from .valueclasses import ScalarValue
from .writermixin import _WriterMixin


class NinjaSettings(ComparableCommonSettings):
    """Settings for Ninja."""

    def __init__(self) -> None:
        """Initialise a NinjaSettings."""
        self._property_meta = {
            "bin_directory": SettingMeta("BinDir", StringSetting, None, ScalarValue),
        }

    @property
    def bin_directory(self) -> StringSetting:
        """Get the bin directory for Ninja."""
        return self._get_value_via_meta()

    @bin_directory.setter
    def bin_directory(self, value: str) -> None:
        self._set_value_via_meta(value)


class NinjaSettingsReader:
    """Context manager to read Ninja settings from disk."""

    def __init__(self) -> None:
        """Initialise a NinjaSettingsReader."""
        self.group = "Thirdparty/Ninja"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> NinjaSettings:
        """Enter a context manager with a NinjaSettingsReader."""
        self.settings.beginGroup(self.group)
        self._settings_object = NinjaSettings()
        self._settings_object.settings_reader = self
        return self._settings_object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        """Exit a context manager with a NinjaSettingsReader."""
        self.settings.endGroup()
        self._settings_object.settings_reader = None
        del self._settings_object
        if type is None:
            pass
        else:
            # propagate exception
            return False


class NinjaSettingsWriter(_WriterMixin):
    """Context manager to write Ninja settings to disk."""

    def __init__(self) -> None:
        """Initialise a NinjaSettingsWriter."""
        self._reader_for_writer = NinjaSettingsReader()
