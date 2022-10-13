#!/usr/bin/env python3

"""
Settings context managers for shortcuts
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


class ShortcutSettings(ComparableCommonSettings):
    """
    Settings for keyboard shortcuts
    """

    def __init__(self) -> None:
        self._property_meta = {
            "conan_create": SettingMeta(
                "Conan/Create", StringSetting, "Alt+C", ScalarValue
            ),
            "conan_create_updates": SettingMeta(
                "Conan/CreateUpdate", StringSetting, "Shift+Alt+C", ScalarValue
            ),
            "conan_imports": SettingMeta(
                "Conan/Imports", StringSetting, "Alt+M", ScalarValue
            ),
            "conan_install": SettingMeta(
                "Conan/Install", StringSetting, "Alt+I", ScalarValue
            ),
            "conan_install_updates": SettingMeta(
                "Conan/InstallUpdate", StringSetting, "Shift+Alt+I", ScalarValue
            ),
            "conan_source": SettingMeta(
                "Conan/Source", StringSetting, "Alt+S", ScalarValue
            ),
            "conan_build": SettingMeta(
                "Conan/Build", StringSetting, "Alt+B", ScalarValue
            ),
            "conan_package": SettingMeta(
                "Conan/Package", StringSetting, "Alt+P", ScalarValue
            ),
            "conan_export_package": SettingMeta(
                "Conan/ExportPackage", StringSetting, "Alt+X", ScalarValue
            ),
            "conan_test_package": SettingMeta(
                "Conan/TestPackage", StringSetting, "Alt+T", ScalarValue
            ),
            "conan_remove_package": SettingMeta(
                "Conan/RemovePackage", StringSetting, "Alt+-", ScalarValue
            ),
            "cancel": SettingMeta("Cancel", StringSetting, "Meta+C", ScalarValue),
            "cmake_build_tool": SettingMeta(
                "CMake/RunBuildTool", StringSetting, "Meta+B", ScalarValue
            ),
            "cmake_build_tool_verbose": SettingMeta(
                "CMake/RunBuildToolVerbose", StringSetting, "Shift+Meta+B", ScalarValue
            ),
            "delete_cmake_cache": SettingMeta(
                "CMake/DeleteCacheFile", StringSetting, "Meta+X", ScalarValue
            ),
        }

    @property
    def conan_create(self) -> StringSetting:
        """
        Get the shortcut for 'conan create'
        """
        return self._get_value_via_meta()

    @conan_create.setter
    def conan_create(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_create_updates(self) -> StringSetting:
        """
        Get the shortcut for 'conan create -u'
        """
        return self._get_value_via_meta()

    @conan_create_updates.setter
    def conan_create_updates(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_imports(self) -> StringSetting:
        """
        Get the shortcut for 'conan imports'
        """
        return self._get_value_via_meta()

    @conan_imports.setter
    def conan_imports(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_install(self) -> StringSetting:
        """
        Get the shortcut for 'conan install'
        """
        return self._get_value_via_meta()

    @conan_install.setter
    def conan_install(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_install_updates(self) -> StringSetting:
        """
        Get the shortcut for 'conan install -u'
        """
        return self._get_value_via_meta()

    @conan_install_updates.setter
    def conan_install_updates(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_source(self) -> StringSetting:
        """
        Get the shortcut for 'conan source'
        """
        return self._get_value_via_meta()

    @conan_source.setter
    def conan_source(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_build(self) -> StringSetting:
        """
        Get the shortcut for 'conan build'
        """
        return self._get_value_via_meta()

    @conan_build.setter
    def conan_build(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_package(self) -> StringSetting:
        """
        Get the shortcut for 'conan package'
        """
        return self._get_value_via_meta()

    @conan_package.setter
    def conan_package(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_export_package(self) -> StringSetting:
        """
        Get the shortcut for 'conan export-pkg'
        """
        return self._get_value_via_meta()

    @conan_export_package.setter
    def conan_export_package(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_test_package(self) -> StringSetting:
        """
        Get the shortcut for 'conan test'
        """
        return self._get_value_via_meta()

    @conan_test_package.setter
    def conan_test_package(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def conan_remove_package(self) -> StringSetting:
        """
        Get the shortcut for 'conan remove'
        """
        return self._get_value_via_meta()

    @conan_remove_package.setter
    def conan_remove_package(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def cancel(self) -> StringSetting:
        """
        Get the shortcut for cancelling the current command
        """
        return self._get_value_via_meta()

    @cancel.setter
    def cancel(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def cmake_build_tool(self) -> StringSetting:
        """
        Get the shortcut for running the CMake build tool
        """
        return self._get_value_via_meta()

    @cmake_build_tool.setter
    def cmake_build_tool(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def cmake_build_tool_verbose(self) -> StringSetting:
        """
        Get the shortcut for CMake build tool in verbose
        """
        return self._get_value_via_meta()

    @cmake_build_tool_verbose.setter
    def cmake_build_tool_verbose(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def delete_cmake_cache(self) -> StringSetting:
        """
        Get the shortcut for deleting the CMake cache
        """
        return self._get_value_via_meta()

    @delete_cmake_cache.setter
    def delete_cmake_cache(self, value: str) -> None:
        self._set_value_via_meta(value)


class ShortcutSettingsReader:
    """
    Context manager to read shortcuts from disk
    """

    def __init__(self) -> None:
        self.settings = BaseSettings.make_settings()
        self.group = "Shortcut"

    def __enter__(self) -> ShortcutSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = ShortcutSettings()
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


class ShortcutSettingsWriter(_WriterMixin):
    """
    Context manager to write shortcuts to disk
    """

    def __init__(self) -> None:
        self._reader_for_writer = ShortcutSettingsReader()
