#!/usr/bin/env python3

"""
Settings context managers for conan preferences
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


class ConanSettings(ComparableCommonSettings):
    """
    Representation of Conan settings on disk
    """

    def __init__(self) -> None:
        self._property_meta = {
            "log_level": SettingMeta(
                "Log/Level", StringSetting, "CRITICAL", ScalarValue
            ),
            "conandata_version_yaml_pathsegment": SettingMeta(
                "ConanData/VersionExtractionPathSegment",
                StringSetting,
                "sources",
                ScalarValue,
            ),
        }

    @property
    def log_level(self) -> StringSetting:
        """
        Get the logging level used for Conan
        """
        return self._get_value_via_meta()

    @log_level.setter
    def log_level(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conandata_version_yaml_pathsegment(self) -> StringSetting:
        """
        Get the YAML segment used to reference the 'version' element in conandata.yml
        """
        return self._get_value_via_meta()

    @conandata_version_yaml_pathsegment.setter
    def conandata_version_yaml_pathsegment(self, value: str) -> None:
        self._set_value_via_meta(value)


class ConanSettingsReader:
    """
    Context manager for reading Conan settings from disk
    """

    def __init__(self) -> None:
        self.settings = BaseSettings.make_settings()
        self.group = "Conan"

    def __enter__(self) -> ConanSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = ConanSettings()
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


class ConanSettingsWriter(_WriterMixin):
    """
    Utility class for writing changed Conan settings to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = ConanSettingsReader()
