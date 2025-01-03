#!/usr/bin/env python3

"""Settings context managers for font preferences."""

import typing
from enum import Enum

from .basesettings import (
    BaseSettings,
    ComparableCommonSettings,
    IntSetting,
    SettingMeta,
    StringSetting,
)
from .valueclasses import ScalarValue
from .writermixin import _WriterMixin


class FontUsage(Enum):
    """Each font usage intended."""

    UI = "UIFont"
    OUTPUT = "OutputPaneFont"


class FontSettings(ComparableCommonSettings):
    """Representation of font settings."""

    def __init__(self) -> None:
        """Initialise a FontSettings."""
        super().__init__()
        self._property_meta = {
            "name": SettingMeta("FontName", StringSetting, None, ScalarValue),
            "size": SettingMeta("FontSize", IntSetting, None, ScalarValue),
        }

    @property
    def name(self) -> StringSetting:
        """Get the name of the font."""
        return self._get_value_via_meta()

    @name.setter
    def name(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def size(self) -> IntSetting:
        """Get the size of the font."""
        return self._get_value_via_meta()

    @size.setter
    def size(self, value: int) -> None:
        self._set_value_via_meta(value)


class FontSettingsReader:
    """Context manager to read font settings from disk."""

    def __init__(self, usage: FontUsage) -> None:
        """Initialise a FontSettingsReader."""
        self.settings = BaseSettings.make_settings()
        self.group = usage.value

    def __enter__(self) -> FontSettings:
        """Enter a context manager with a FontSettingsReader."""
        self.settings.beginGroup(self.group)
        self._settings_object = FontSettings()
        self._settings_object.settings_reader = self
        return self._settings_object

    def __exit__(
        self, exc_type: typing.Any, exc_value: typing.Any, exc_traceback: typing.Any
    ) -> typing.Any:
        """Exit a context manager with a FontSettingsReader."""
        self.settings.endGroup()
        self._settings_object.settings_reader = None
        del self._settings_object
        if exc_type is not None:
            # propagate exception
            return False
        return True


class FontSettingsWriter(_WriterMixin):
    """Utility class for writing font settings to disk."""

    def __init__(self, usage: FontUsage) -> None:
        """Initialise a FontSettingsWriter."""
        self._reader_for_writer = FontSettingsReader(usage)
