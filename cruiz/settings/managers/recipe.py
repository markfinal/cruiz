#!/usr/bin/env python3

"""
Settings context manager for recipes
"""

from __future__ import annotations

from multiprocessing import cpu_count
import pathlib
import typing

from qtpy import QtCore
from cruiz.constants import CompilerCacheTypes
from cruiz.exceptions import InconsistentSettingsError

from cruiz.recipe.recipe import Recipe

from .basesettings import (
    BaseSettings,
    BoolSetting,
    StringSetting,
    IntSetting,
    DictSetting,
    WorkflowCwd,
    WorkflowCwdSetting,
    ComparableCommonSettings,
    SettingMeta,
)
from .writermixin import _WriterMixin
from .valueclasses import ScalarValue, DictValue


class RecipeSettings(ComparableCommonSettings):
    """
    Representation of recipe settings
    """

    @classmethod
    def from_recipe(cls, recipe: Recipe) -> RecipeSettings:
        """
        Create an instance using a recipe
        """
        instance = cls()
        instance._recipe = recipe
        return instance

    @classmethod
    def from_uuid(cls, uuid: QtCore.QUuid) -> RecipeSettings:
        """
        Create an instance using a UUID
        """
        instance = cls()
        instance._uuid = uuid
        return instance

    def __init__(self) -> None:
        super().__init__()
        self._uuid: typing.Optional[QtCore.QUuid] = None
        self._recipe: typing.Optional[Recipe] = None

        if self._recipe:
            default_profile = self._recipe.context.default_profile_filename()  # type: ignore[unreachable]  # noqa: E501
        else:
            try:
                context = self.settings_reader.recipe.context  # type: ignore
                default_profile = context.default_profile_filename()
            except AttributeError:
                # this copes with there not being a context assigned
                # a recipe upon first load
                default_profile = None

        self._property_meta = {
            "path": SettingMeta("Path", StringSetting, None, ScalarValue),
            "local_cache_name": SettingMeta(
                "LocalCacheName", StringSetting, None, ScalarValue
            ),
            "profile": SettingMeta(
                "Profile", StringSetting, default_profile, ScalarValue
            ),
            "num_cpu_cores": SettingMeta(
                "NumberOfCores", IntSetting, cpu_count(), ScalarValue
            ),
            "options": SettingMeta("Options", DictSetting, {}, DictValue),
            "attribute_overrides": SettingMeta(
                "Attributes", DictSetting, {}, DictValue
            ),
            "local_workflow_cwd": SettingMeta(
                "LocalWorkflow/Cwd",
                WorkflowCwdSetting,
                WorkflowCwd.RELATIVE_TO_RECIPE,
                ScalarValue,
            ),
            "local_workflow_common_subdir": SettingMeta(
                "LocalWorkflow/CommonSubdirectory", StringSetting, None, ScalarValue
            ),
            "local_workflow_install_folder": SettingMeta(
                "LocalWorkflow/CustomInstallSubdirectory",
                StringSetting,
                None,
                ScalarValue,
            ),
            "local_workflow_imports_folder": SettingMeta(
                "LocalWorkflow/CustomImportsSubdirectory",
                StringSetting,
                None,
                ScalarValue,
            ),
            "local_workflow_source_folder": SettingMeta(
                "LocalWorkflow/CustomSourceSubdirectory",
                StringSetting,
                None,
                ScalarValue,
            ),
            "local_workflow_build_folder": SettingMeta(
                "LocalWorkflow/CustomBuildSubdirectory",
                StringSetting,
                None,
                ScalarValue,
            ),
            "local_workflow_package_folder": SettingMeta(
                "LocalWorkflow/CustomPackageSubdirectory",
                StringSetting,
                None,
                ScalarValue,
            ),
            "local_workflow_test_folder": SettingMeta(
                "LocalWorkflow/CustomTestSubdirectory", StringSetting, None, ScalarValue
            ),
            "cmake_find_debug": SettingMeta(
                "CMake/FindDebug", BoolSetting, False, ScalarValue
            ),
            "cmake_verbose": SettingMeta(
                "CMake/Verbose", BoolSetting, False, ScalarValue
            ),
            "compiler_cache": SettingMeta(
                "CompilerCache", StringSetting, None, ScalarValue
            ),
            "compilercache_autotools_configuration": SettingMeta(
                "CompilerCacheAutoToolsConfig", DictSetting, {}, DictValue
            ),
        }

    @property
    def all_uuids(self) -> typing.List[QtCore.QUuid]:
        """
        Get all UUIDs that have settings.
        """
        settings = BaseSettings.make_settings()
        settings.beginGroup("Recipe")
        uuids = settings.childGroups()
        settings.endGroup()
        uuid_list: typing.List[QtCore.QUuid] = []
        for uuid in uuids:
            uuid_list.append(QtCore.QUuid(uuid))
        return uuid_list

    def matching_uuids(self, recipe_path: pathlib.Path) -> typing.List[QtCore.QUuid]:
        """
        Get UUIDs matching the recipe path provided.
        """
        # TODO: context management around groups would be beneficial here
        settings = BaseSettings.make_settings()
        settings.beginGroup("Recipe")
        uuids = settings.childGroups()
        matches: typing.List[QtCore.QUuid] = []
        for uuid in uuids:
            settings.beginGroup(uuid)
            path = settings.value("Path")
            if not isinstance(path, str):
                raise InconsistentSettingsError()
            if pathlib.Path(path) == recipe_path:
                matches.append(QtCore.QUuid(uuid))
            settings.endGroup()
        settings.endGroup()
        return matches

    @property
    def path(self) -> StringSetting:
        """
        Get the path of the recipe
        """
        return self._get_value_via_meta()

    @path.setter
    def path(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_cache_name(self) -> StringSetting:
        """
        Get the associated local cache name
        """
        return self._get_value_via_meta()

    @local_cache_name.setter
    def local_cache_name(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def profile(self) -> StringSetting:
        """
        Get the profile currently used by the recipe
        """
        return self._get_value_via_meta()

    @profile.setter
    def profile(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def num_cpu_cores(self) -> IntSetting:
        """
        Get the number of CPU cores used by the recipe
        """
        return self._get_value_via_meta()

    @num_cpu_cores.setter
    def num_cpu_cores(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def options(self) -> DictSetting:
        """
        Get the dictionary of recipe options
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "Options"
        options: typing.Dict[str, typing.Any] = {}
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            for i in range(count):
                settings.setArrayIndex(i)
                name = settings.value("Option")
                value = settings.value("Value")
                assert isinstance(name, str)
                options[name] = value
        return DictSetting(options, {})

    def append_options(self, options: DictSetting) -> None:
        """
        Append new option settings

        self.__options set at the end of the function, but in case this is called
        several times, read at the start too
        """
        try:
            existing_options, prop, real_key = self.__options  # type: ignore
        except AttributeError:
            existing_options = {}
            prop = "options"
            real_key = "Options"
        existing_options.update(options)
        # avoids private name mangling
        setattr(  # noqa: B010
            self,
            "__options",
            DictValue(existing_options, prop, real_key, "Option", "Value"),
        )

    @property
    def attribute_overrides(self) -> DictSetting:
        """
        Get the dictionary of attributes
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "Attributes"
        attributes: typing.Dict[str, typing.Any] = {}
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            for i in range(count):
                settings.setArrayIndex(i)
                name = settings.value("Attribute")
                value = settings.value("Value")
                assert isinstance(name, str)
                attributes[name] = value
        return DictSetting(attributes, {})

    def append_attribute(self, attributes: DictSetting) -> None:
        """
        Append new attributes

        self.__attributes set at the end of the function, but in case this is called
        several times, read at the start too
        """
        try:
            existing_attributes, prop, real_key = self.__attributes  # type: ignore
        except AttributeError:
            existing_attributes = {}
            prop = "attribute_overrides"
            real_key = "Attributes"
        existing_attributes.update(attributes)
        # avoids private name mangling
        setattr(  # noqa: B010
            self,
            "__attributes",
            DictValue(existing_attributes, prop, real_key, "Attribute", "Value"),
        )

    @property
    def local_workflow_cwd(self) -> WorkflowCwdSetting:
        """
        Get the local workflow current working directory
        """
        return self._get_value_via_meta()

    @local_workflow_cwd.setter
    def local_workflow_cwd(self, value: WorkflowCwd) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_common_subdir(self) -> StringSetting:
        """
        Get the local workflow common subdirectory to build into
        """
        return self._get_value_via_meta()

    @local_workflow_common_subdir.setter
    def local_workflow_common_subdir(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_install_folder(self) -> StringSetting:
        """
        Get the local workflow Conan install folder
        """
        return self._get_value_via_meta()

    @local_workflow_install_folder.setter
    def local_workflow_install_folder(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_imports_folder(self) -> StringSetting:
        """
        Get the local workflow Conan imports folder
        """
        return self._get_value_via_meta()

    @local_workflow_imports_folder.setter
    def local_workflow_imports_folder(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_source_folder(self) -> StringSetting:
        """
        Get the local workflow Conan source folder
        """
        return self._get_value_via_meta()

    @local_workflow_source_folder.setter
    def local_workflow_source_folder(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_build_folder(self) -> StringSetting:
        """
        Get the local workflow Conan build folder
        """
        return self._get_value_via_meta()

    @local_workflow_build_folder.setter
    def local_workflow_build_folder(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_package_folder(self) -> StringSetting:
        """
        Get the local workflow Conan package folder
        """
        return self._get_value_via_meta()

    @local_workflow_package_folder.setter
    def local_workflow_package_folder(self, value: str) -> None:
        self._set_value_via_meta(value)

    @property
    def local_workflow_test_folder(self) -> StringSetting:
        """
        Get the local workflow Conan test folder
        """
        return self._get_value_via_meta()

    @local_workflow_test_folder.setter
    def local_workflow_test_folder(self, value: str) -> None:
        self._set_value_via_meta(value)

    # TODO: not sure if this is quite how I want to write it
    # also editables are not part of the current UI
    @property
    def editables_count(self) -> IntSetting:
        """
        Get the number of editables in this recipe
        """
        key = "Editables"
        assert self.settings_reader
        with BaseSettings.ReadArray(key, settings=self.settings_reader.settings) as (
            _,
            count,
        ):
            return IntSetting(count, 0)

    @property
    def cmake_find_debug(self) -> BoolSetting:
        """
        Get whether CMake find debug is enabled for this recipe
        """
        return self._get_value_via_meta()

    @cmake_find_debug.setter
    def cmake_find_debug(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def cmake_verbose(self) -> BoolSetting:
        """
        Get whether CMake verbose mode is enabled for this recipe
        """
        return self._get_value_via_meta()

    @cmake_verbose.setter
    def cmake_verbose(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def compiler_cache(self) -> StringSetting:
        """
        Get the compiler cache in use with this recipe
        """
        return self._get_value_via_meta()

    @compiler_cache.setter
    def compiler_cache(self, value: bool) -> None:
        self._set_value_via_meta(value)

    @property
    def compilercache_autotools_configuration(self) -> DictSetting:
        """
        Get the dictionary of autotools configuration for this recipe
        """
        assert self.settings_reader
        settings = self.settings_reader.settings
        key = "CompilerCacheAutoToolsConfig"
        config: typing.Dict[str, typing.Any] = {}
        with BaseSettings.ReadArray(key, settings=settings) as (settings, count):
            for i in range(count):
                settings.setArrayIndex(i)
                name = settings.value("CompileCache")  # TODO: note the typo
                value = settings.value("ConfigureArgs")
                assert isinstance(name, str)
                config[name] = value
        return DictSetting(config, {})

    def append_compilercache_autotools_configuration(
        self, cache: CompilerCacheTypes, arguments: typing.Optional[str]
    ) -> None:
        """
        Append new autotools compiler cache configurations

        self.__compilercache_autotools_config set at the end of the function,
        but in case this is called several times, read at the start too
        """
        try:
            (
                existing_config,
                prop,
                real_key,
                _,
                _,
            ) = self.__compilercache_autotools_config  # type: ignore
        except AttributeError:
            existing_config = {}
            prop = "compilercache_autotools_configuration"
            real_key = "CompilerCacheAutoToolsConfig"
        existing_config[cache.name] = arguments
        # avoids private name mangling
        setattr(  # noqa: B010
            self,
            "__compilercache_autotools_config",
            DictValue(existing_config, prop, real_key, "CompileCache", "ConfigureArgs"),
        )


class RecipeSettingsReader:
    """
    Context manager for reading recipe settings from disk
    """

    @classmethod
    def from_recipe(cls, recipe: Recipe) -> RecipeSettingsReader:
        """
        Create an instance using a recipe
        """
        return cls(recipe, recipe.uuid)

    @classmethod
    def from_uuid(cls, uuid: QtCore.QUuid) -> RecipeSettingsReader:
        """
        Create an instance using a UUID
        """
        return cls(None, uuid)

    def __init__(self, recipe: typing.Optional[Recipe], uuid: QtCore.QUuid) -> None:
        self.recipe = recipe
        self._uuid = uuid
        self.group = f"Recipe/{uuid.toString(QtCore.QUuid.WithoutBraces)}"
        self.settings = BaseSettings.make_settings()

    def __enter__(self) -> RecipeSettings:
        self.settings.beginGroup(self.group)
        self._settings_object = (
            RecipeSettings.from_recipe(self.recipe)
            if self.recipe
            else RecipeSettings.from_uuid(self._uuid)
        )
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


class RecipeSettingsWriter(_WriterMixin):
    """
    Utiiity for writing current recipe settings to disk
    """

    @classmethod
    def from_recipe(cls, recipe: Recipe) -> RecipeSettingsWriter:
        """
        Create an instance using a recipe
        """
        instance = cls()
        instance._reader_for_writer = RecipeSettingsReader.from_recipe(recipe)
        return instance

    @classmethod
    def from_uuid(cls, uuid: QtCore.QUuid) -> RecipeSettingsWriter:
        """
        Create an instance using a UUID
        """
        instance = cls()
        instance._reader_for_writer = RecipeSettingsReader.from_uuid(uuid)
        return instance


class RecipeSettingsDeleter:
    """
    Utility for deleting all recipe settings, associated by a UUID, from disk
    """

    def __init__(self) -> None:
        self._settings = BaseSettings.make_settings()

    def delete(self, uuid: QtCore.QUuid) -> None:
        """
        Delete the recipe settings from the specified UUID
        """
        group = f"Recipe/{uuid.toString(QtCore.QUuid.WithoutBraces)}"
        self._settings.remove(group)
