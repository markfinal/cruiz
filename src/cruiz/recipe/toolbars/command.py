#!/usr/bin/env python3

"""Recipe command toolbar."""

import os
import typing
from io import StringIO

from PySide6 import QtCore, QtGui, QtWidgets

import cruiz.globals
import cruiz.workers.api as workers_api
from cruiz.constants import BuildFeatureConstants, CompilerCacheTypes
from cruiz.environ import EnvironSaver
from cruiz.exceptions import RecipeInspectionError
from cruiz.interop.commandparameters import CommandParameters
from cruiz.settings.managers.compilercachepreferences import CompilerCacheSettingsReader
from cruiz.settings.managers.generalpreferences import GeneralSettingsReader
from cruiz.settings.managers.recipe import RecipeSettings, RecipeSettingsReader
from cruiz.settings.managers.shortcuts import ShortcutSettingsReader


IS_CONAN_V1 = cruiz.globals.CONAN_MAJOR_VERSION == 1


class RecipeCommandToolbar(QtWidgets.QToolBar):
    """QToolBar representing the recipe commands."""

    command_started = QtCore.Signal()
    command_ended = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget) -> None:
        """Initialise a RecipeCommandToolbar."""
        super().__init__(parent)
        recipe_ui = parent._ui  # type: ignore[attr-defined]
        self.command_started.connect(self._command_started)
        self.command_ended.connect(self._command_ended)
        self._idle_group = QtGui.QActionGroup(self)
        self._idle_group.setEnabled(True)
        self._cancel_command_group = QtGui.QActionGroup(self)
        self._cancel_command_group.setEnabled(False)
        self._add_toolbutton(
            [recipe_ui.actionCreateCommand, recipe_ui.actionCreateUpdateCommand]
        )
        self.addSeparator()
        self._add_toolbutton(
            [recipe_ui.actionInstallCommand, recipe_ui.actionInstallUpdateCommand]
        )
        if IS_CONAN_V1:
            self._add_toolbutton([recipe_ui.actionImportsCommand])
        else:
            recipe_ui.actionImportsCommand.setVisible(False)
        self._add_toolbutton([recipe_ui.actionSourceCommand])
        self._add_toolbutton([recipe_ui.actionBuildCommand])
        if IS_CONAN_V1:
            self._add_toolbutton([recipe_ui.actionPackageCommand])
        else:
            recipe_ui.actionPackageCommand.setVisible(False)
        self._add_toolbutton([recipe_ui.actionExportPackageCommand])
        self._add_toolbutton([recipe_ui.actionTestCommand])
        self.addSeparator()
        self._add_toolbutton([recipe_ui.actionCancelCommand], for_cancel_group=True)
        self.addSeparator()
        self._add_toolbutton([recipe_ui.actionRemovePackageCommand])
        self.addSeparator()
        if IS_CONAN_V1:
            self._add_toolbutton(
                [
                    recipe_ui.actionCMakeBuildToolCommand,
                    recipe_ui.actionCMakeBuildToolVerboseCommand,
                    recipe_ui.actionCMakeRemoveCacheCommand,
                ]
            )
        else:
            recipe_ui.actionCMakeBuildToolCommand.setEnabled(False)
            recipe_ui.actionCMakeBuildToolVerboseCommand.setEnabled(False)
            recipe_ui.actionCMakeRemoveCacheCommand.setEnabled(False)

    @property
    def _recipe_widget(self) -> QtCore.QObject:
        return self.parent()

    def _add_toolbutton(
        self, actions: typing.List[QtGui.QAction], for_cancel_group: bool = False
    ) -> None:
        assert actions
        button = QtWidgets.QToolButton()
        button.addActions(actions)
        button.setDefaultAction(actions[0])
        self.addWidget(button)
        if for_cancel_group:
            for action in actions:
                self._cancel_command_group.addAction(action)
        else:
            for action in actions:
                self._idle_group.addAction(action)

    def configure_actions(self) -> None:
        """Configure the QActions in the toolbar."""

        def _configure(
            action: QtGui.QAction, trigger_slot: typing.Callable[[], None]
        ) -> None:
            action.setShortcutVisibleInContextMenu(True)
            action.setShortcutContext(QtCore.Qt.ShortcutContext.WindowShortcut)
            action.triggered.connect(trigger_slot)

        # shortcuts themselves are set elsewhere, as they can be dynamic
        # through the lifetime of the application
        # TODO: the _ui is likely to be on the RecipeWidget
        # pylint: disable=protected-access
        recipe_ui = self.parent()._ui  # type: ignore[attr-defined]

        _configure(recipe_ui.actionCreateCommand, self._conan_create)
        _configure(recipe_ui.actionCreateUpdateCommand, self._conan_create_update)
        _configure(recipe_ui.actionInstallCommand, self._conan_install)
        _configure(recipe_ui.actionInstallUpdateCommand, self._conan_install_update)
        if IS_CONAN_V1:
            _configure(recipe_ui.actionImportsCommand, self._conan_imports)
        _configure(recipe_ui.actionSourceCommand, self._conan_source)
        _configure(recipe_ui.actionBuildCommand, self._conan_build)
        if IS_CONAN_V1:
            _configure(recipe_ui.actionPackageCommand, self._conan_package)
        _configure(recipe_ui.actionExportPackageCommand, self._conan_export_package)
        _configure(recipe_ui.actionTestCommand, self._conan_test)
        _configure(recipe_ui.actionCancelCommand, self._cancel_command)
        _configure(recipe_ui.actionRemovePackageCommand, self._conan_remove)
        if IS_CONAN_V1:
            _configure(recipe_ui.actionCMakeBuildToolCommand, self._cmake_build)
            _configure(
                recipe_ui.actionCMakeBuildToolVerboseCommand, self._cmake_build_verbose
            )
            _configure(
                recipe_ui.actionCMakeRemoveCacheCommand, self._cmake_remove_cache
            )

    def disable_all_actions(self) -> None:
        """Disable everything in the case of recipe loading errors."""
        self._idle_group.setEnabled(False)
        self._cancel_command_group.setEnabled(False)

    def refresh_action_shortcuts_and_tooltips(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> None:
        """Refresh all command action shortcuts and tooltips."""
        with ShortcutSettingsReader() as settings:
            conan_create = settings.conan_create.resolve()
            conan_create_updates = settings.conan_create_updates.resolve()
            conan_install = settings.conan_install.resolve()
            conan_install_updates = settings.conan_install_updates.resolve()
            if IS_CONAN_V1:
                conan_imports = settings.conan_imports.resolve()
            conan_source = settings.conan_source.resolve()
            conan_build = settings.conan_build.resolve()
            if IS_CONAN_V1:
                conan_package = settings.conan_package.resolve()
            conan_exportpkg = settings.conan_export_package.resolve()
            conan_test = settings.conan_test_package.resolve()
            cancel = settings.cancel.resolve()
            conan_remove = settings.conan_remove_package.resolve()
            if IS_CONAN_V1:
                cmake_build_tool = settings.cmake_build_tool.resolve()
                cmake_build_tool_verbose = settings.cmake_build_tool_verbose.resolve()
                remove_cmakecache = settings.delete_cmake_cache.resolve()

        def _configure_conan_action(
            action: QtGui.QAction,
            shortcut: str,
            params: CommandParameters,
            icon_path: str,
        ) -> None:
            action.setShortcut(QtGui.QKeySequence(shortcut))
            action.setToolTip(self._generate_command_tooltip(params))
            if icon_path.startswith(":/"):
                icon = QtGui.QIcon(icon_path)
            else:
                icon = QtGui.QIcon(f":/icons/{cruiz.globals.get_theme()}/{icon_path}")
            action.setIcon(icon)

        # pylint: disable=protected-access
        recipe_ui = self.parent()._ui  # type: ignore[attr-defined]
        _configure_conan_action(
            recipe_ui.actionCreateCommand,
            conan_create,
            self._make_conan_create_params(recipe_attributes, None),
            "create.svg",
        )
        _configure_conan_action(
            recipe_ui.actionCreateUpdateCommand,
            conan_create_updates,
            self._make_conan_create_params(recipe_attributes, ["-u"]),
            "create.svg",
        )
        _configure_conan_action(
            recipe_ui.actionInstallCommand,
            conan_install,
            self._make_conan_install_params(recipe_attributes, None),
            "install.svg",
        )
        _configure_conan_action(
            recipe_ui.actionInstallUpdateCommand,
            conan_install_updates,
            self._make_conan_install_params(recipe_attributes, ["-u"]),
            "install.svg",
        )
        if IS_CONAN_V1:
            _configure_conan_action(
                recipe_ui.actionImportsCommand,
                conan_imports,
                self._make_conan_imports_params(recipe_attributes),
                "imports.svg",
            )
        _configure_conan_action(
            recipe_ui.actionSourceCommand,
            conan_source,
            self._make_conan_source_params(recipe_attributes),
            "source.svg",
        )
        _configure_conan_action(
            recipe_ui.actionBuildCommand,
            conan_build,
            self._make_conan_build_params(recipe_attributes),
            "build.svg",
        )
        if IS_CONAN_V1:
            _configure_conan_action(
                recipe_ui.actionPackageCommand,
                conan_package,
                self._make_conan_package_params(recipe_attributes),
                "package.svg",
            )
        _configure_conan_action(
            recipe_ui.actionExportPackageCommand,
            conan_exportpkg,
            self._make_conan_export_package_params(recipe_attributes),
            "exportpackage.svg",
        )
        _configure_conan_action(
            recipe_ui.actionTestCommand,
            conan_test,
            self._make_conan_test_package_params(recipe_attributes),
            "testpackage.svg",
        )
        _configure_conan_action(
            recipe_ui.actionRemovePackageCommand,
            conan_remove,
            self._make_conan_remove_package_params(recipe_attributes),
            "removepackage.svg",
        )

        def _configure_non_conan_action(
            action: QtGui.QAction, shortcut: str, tooltip: str, icon_path: str
        ) -> None:
            action.setShortcut(QtGui.QKeySequence(shortcut))
            action.setToolTip(tooltip)
            if icon_path.startswith(":/"):
                icon = QtGui.QIcon(icon_path)
            else:
                icon = QtGui.QIcon(f":/icons/{cruiz.globals.get_theme()}/{icon_path}")
            action.setIcon(icon)

        _configure_non_conan_action(
            recipe_ui.actionCancelCommand,
            cancel,
            "Cancel the currently running command",
            ":/cancel.svg",
        )

        if IS_CONAN_V1:
            _configure_non_conan_action(
                recipe_ui.actionCMakeBuildToolCommand,
                cmake_build_tool,
                "CMake build",
                ":/cmakebuildtool.svg",
            )

            _configure_non_conan_action(
                recipe_ui.actionCMakeBuildToolVerboseCommand,
                cmake_build_tool_verbose,
                "CMake verbose build",
                ":/cmakebuildtoolverbose.svg",
            )

            _configure_non_conan_action(
                recipe_ui.actionCMakeRemoveCacheCommand,
                remove_cmakecache,
                "Remove CMake cache",
                ":/removecmakecache.svg",
            )

    def _command_started(self) -> None:
        self._idle_group.setEnabled(False)
        self._cancel_command_group.setEnabled(True)

    def _command_ended(self) -> None:
        self._idle_group.setEnabled(True)
        self._cancel_command_group.setEnabled(False)

    def _append_build_features(
        self, params: CommandParameters, settings: RecipeSettings
    ) -> None:
        if settings.cmake_find_debug.resolve():
            params.set_build_feature(BuildFeatureConstants.CMAKEFINDDEBUGMODE, "ON")
        if settings.cmake_verbose.resolve():
            params.set_build_feature(BuildFeatureConstants.CMAKEVERBOSEMODE, "ON")
        compilercache_autotools_config = (
            settings.compilercache_autotools_configuration.resolve()
        )

        def _find_executable(suggested_dir: str, executable_name: str) -> str:
            with EnvironSaver():
                if suggested_dir:
                    os.environ["PATH"] = (
                        QtCore.QDir.toNativeSeparators(suggested_dir)
                        + os.pathsep
                        + os.environ.get("PATH", "")
                    )
                exe_path = QtCore.QStandardPaths.findExecutable(executable_name)
                return exe_path

        compiler_cache = settings.compiler_cache.resolve()
        if compiler_cache == CompilerCacheTypes.CCACHE.value:
            with CompilerCacheSettingsReader() as settings_compilercache:
                ccache_dir = settings_compilercache.ccache_bin_directory.resolve()
            executable = _find_executable(ccache_dir, "ccache")
            if executable:
                params.set_build_feature(
                    BuildFeatureConstants.CCACHEEXECUTABLE, executable
                )
                if CompilerCacheTypes.CCACHE.name in compilercache_autotools_config:
                    params.set_build_feature(
                        BuildFeatureConstants.CCACHEAUTOTOOLSCONFIGARGS,
                        compilercache_autotools_config[CompilerCacheTypes.CCACHE.name],
                    )
        elif compiler_cache == CompilerCacheTypes.SCCACHE.value:
            with CompilerCacheSettingsReader() as settings_compilercache:
                sccache_dir = settings_compilercache.sccache_bin_directory.resolve()
            executable = _find_executable(sccache_dir, "sccache")
            if executable:
                params.set_build_feature(
                    BuildFeatureConstants.SCCACHEEXECUTABLE, executable
                )
                if CompilerCacheTypes.SCCACHE.name in compilercache_autotools_config:
                    params.set_build_feature(
                        BuildFeatureConstants.SCCACHEAUTOTOOLSCONFIGARGS,
                        compilercache_autotools_config[CompilerCacheTypes.SCCACHE.name],
                    )
        elif compiler_cache == CompilerCacheTypes.BUILDCACHE.value:
            with CompilerCacheSettingsReader() as settings_compilercache:
                buildcache_dir = (
                    settings_compilercache.buildcache_bin_directory.resolve()
                )
            executable = _find_executable(buildcache_dir, "buildcache")
            if executable:
                params.set_build_feature(
                    BuildFeatureConstants.BUILDCACHEEXECUTABLE, executable
                )
                if CompilerCacheTypes.BUILDCACHE.name in compilercache_autotools_config:
                    params.set_build_feature(
                        BuildFeatureConstants.BUILDCACHEAUTOTOOLSCONFIGARGS,
                        compilercache_autotools_config[
                            CompilerCacheTypes.BUILDCACHE.name
                        ],
                    )

    def _append_general_prefs(self, params: CommandParameters) -> None:
        with GeneralSettingsReader() as settings:
            params.time_commands = settings.enable_command_timing.resolve()

    def _make_common_params(
        self,
        verb: str,
        worker: typing.Union[
            typing.Callable[[typing.Any, typing.Any], None],
            typing.Callable[[typing.Any, typing.Any, typing.Any], None],
        ],
        recipe_attributes: typing.Dict[str, typing.Optional[str]],
        with_recipe_path: bool = True,
        with_pkgref: bool = False,
        with_cwd: bool = False,
        with_profile: bool = False,
        with_install_folder: bool = False,
        with_imports_folder: bool = False,
        with_source_folder: bool = False,
        fudge_source_folder: bool = False,
        with_build_folder: bool = False,
        with_package_folder: bool = False,
        with_test_build_folder: bool = False,
        with_explicit_name: bool = False,
        with_force: bool = False,
        with_exclusive_package_folder: bool = False,
        with_options: bool = False,
        v2_omit_test_folder: bool = False,
        v2_need_reference: bool = False,
    ) -> CommandParameters:
        recipe_widget = self._recipe_widget
        recipe = recipe_widget.recipe  # type: ignore[attr-defined]
        params = CommandParameters(verb, worker)
        if with_recipe_path:
            params.recipe_path = recipe.path
        if with_explicit_name:
            params.name = recipe_attributes.get("name", "unknown-name")
        if with_pkgref:
            params.version = recipe.version or recipe_attributes.get(
                "version", "unknown-version"
            )
            params.user = recipe.user
            params.channel = recipe.channel
            params.make_package_reference()  # only needed for the exported string
        if with_force:
            params.force = True
        if cruiz.globals.CONAN_MAJOR_VERSION > 1:
            params.v2_need_reference = v2_need_reference
        self._append_general_prefs(params)
        with RecipeSettingsReader.from_recipe(recipe) as settings:
            if cruiz.globals.CONAN_MAJOR_VERSION == 1:
                num_cores = settings.num_cpu_cores
                if num_cores.value is not None:
                    params.added_environment.update(
                        {"CONAN_CPU_COUNT": str(num_cores.value)}
                    )
            if with_options:
                for key, value in settings.options.resolve().items():
                    assert recipe_attributes["name"]
                    params.add_option(
                        recipe_attributes["name"], key, value
                    )  # TODO: is this the most efficient algorithm?
                attributes = settings.attribute_overrides.resolve()
                if "extra_config_options" in attributes:
                    for keyvalue in attributes["extra_config_options"].split(","):
                        option_name, option_value = keyvalue.split("=", maxsplit=1)
                        params.add_option(None, option_name, option_value)
            self._append_build_features(params, settings)
            if with_exclusive_package_folder:
                # export-pkg requires
                # - if package_folder is present, do not specify source or build folder
                # - if package_folder is NOT present, you might still need the fudge of
                #   the source folder
                if settings.local_workflow_package_folder.resolve() is None:
                    with_source_folder = True
                    with_build_folder = True
                else:
                    with_source_folder = False
                    with_build_folder = False
                    fudge_source_folder = False
            if with_profile:
                params.profile = settings.profile.resolve()
            if with_cwd:
                workflow_cwd = settings.local_workflow_cwd.resolve()
                common_subdir = settings.local_workflow_common_subdir.resolve()
                params.cwd = recipe_widget.get_working_dir(workflow_cwd, common_subdir)  # type: ignore[attr-defined] # noqa: E501
            if with_install_folder:
                install_folder = settings.local_workflow_install_folder.resolve()
                params.install_folder = recipe_widget.resolve_expression(install_folder)  # type: ignore[attr-defined] # noqa: E501
            if with_imports_folder:
                imports_folder = settings.local_workflow_imports_folder.resolve()
                params.imports_folder = recipe_widget.resolve_expression(imports_folder)  # type: ignore[attr-defined] # noqa: E501
            if with_source_folder:
                source_folder = settings.local_workflow_source_folder.resolve()
                params.source_folder = recipe_widget.resolve_expression(source_folder)  # type: ignore[attr-defined] # noqa: E501
            if fudge_source_folder:
                source_folder = settings.local_workflow_source_folder.resolve()
                if (
                    not source_folder
                    and not recipe_widget.cwd_is_relative_to_recipe(  # type: ignore[attr-defined] # noqa: E501
                        workflow_cwd
                    )
                ):
                    # fudge due to the default source_folder changing between
                    # 'conan source' and 'conan build'
                    source_folder = "."
                params.source_folder = recipe_widget.resolve_expression(source_folder)  # type: ignore[attr-defined] # noqa: E501
            if with_build_folder:
                build_folder = settings.local_workflow_build_folder.resolve()
                params.build_folder = recipe_widget.resolve_expression(build_folder)  # type: ignore[attr-defined] # noqa: E501
            if with_package_folder:
                package_folder = settings.local_workflow_package_folder.resolve()
                params.package_folder = recipe_widget.resolve_expression(package_folder)  # type: ignore[attr-defined] # noqa: E501
            if with_test_build_folder:
                test_folder = settings.local_workflow_test_folder.resolve()
                params.test_build_folder = recipe_widget.resolve_expression(test_folder)  # type: ignore[attr-defined] # noqa: E501
            if cruiz.globals.CONAN_MAJOR_VERSION == 1:
                pass
            else:
                params.v2_omit_test_folder = v2_omit_test_folder
        return params

    def _make_conan_create_params(
        self,
        recipe_attributes: typing.Dict[str, typing.Optional[str]],
        args: typing.Optional[typing.List[str]],
    ) -> CommandParameters:
        params = self._make_common_params(
            "create",
            workers_api.create.invoke,
            recipe_attributes,
            with_pkgref=True,
            with_profile=True,
            with_options=True,
        )
        if args:
            params.arguments.extend(args)
        return params

    def _make_conan_install_params(
        self,
        recipe_attributes: typing.Dict[str, typing.Optional[str]],
        args: typing.Optional[typing.List[str]],
    ) -> CommandParameters:
        params = self._make_common_params(
            "install",
            workers_api.install.invoke,
            recipe_attributes,
            with_pkgref=True,
            with_cwd=True,
            with_profile=True,
            with_install_folder=True,
            with_options=True,
        )
        if args:
            params.arguments.extend(args)
        return params

    def _make_conan_imports_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        return self._make_common_params(
            "imports",
            workers_api.imports.invoke,
            recipe_attributes,
            with_cwd=True,
            with_install_folder=True,
            with_imports_folder=True,
        )

    def _make_conan_source_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        named_args = {}
        if IS_CONAN_V1:
            pass
        else:
            named_args["with_pkgref"] = True
        return self._make_common_params(
            "source",
            workers_api.source.invoke,
            recipe_attributes,
            with_cwd=True,
            with_install_folder=True,
            with_source_folder=True,
            **named_args,
        )

    def _make_conan_build_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        named_args = {}
        if IS_CONAN_V1:
            pass
        else:
            named_args["with_pkgref"] = True
        return self._make_common_params(
            "build",
            workers_api.build.invoke,
            recipe_attributes,
            with_cwd=True,
            with_install_folder=True,
            with_source_folder=True,
            fudge_source_folder=True,
            with_build_folder=True,
            with_package_folder=True,
            **named_args,
        )

    def _make_conan_package_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        return self._make_common_params(
            "package",
            workers_api.package.invoke,
            recipe_attributes,
            with_cwd=True,
            with_install_folder=True,
            with_source_folder=True,
            fudge_source_folder=True,
            with_build_folder=True,
            with_package_folder=True,
        )

    def _make_conan_export_package_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        named_args = {}
        if IS_CONAN_V1:
            named_args["with_force"] = True
        else:
            named_args["v2_omit_test_folder"] = True
        return self._make_common_params(
            "export-pkg",
            workers_api.exportpackage.invoke,
            recipe_attributes,
            with_cwd=True,
            with_pkgref=True,
            with_install_folder=True,
            with_source_folder=True,
            fudge_source_folder=True,
            with_build_folder=True,
            with_package_folder=True,
            with_exclusive_package_folder=True,
            with_explicit_name=True,
            with_options=True,
            **named_args,
        )

    def _make_conan_test_package_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        named_args = {}
        if IS_CONAN_V1:
            pass
        else:
            named_args["v2_need_reference"] = True
        params = self._make_common_params(
            "test",
            workers_api.testpackage.invoke,
            recipe_attributes,
            with_recipe_path=False,
            with_cwd=True,
            with_profile=True,
            with_test_build_folder=True,
            with_explicit_name=True,
            with_pkgref=True,
            with_options=True,
            **named_args,
        )
        recipe_widget = self._recipe_widget
        recipe = recipe_widget.recipe  # type: ignore[attr-defined]
        params.recipe_path = recipe.path.parent / "test_package"
        return params

    def _make_conan_remove_package_params(
        self, recipe_attributes: typing.Dict[str, typing.Optional[str]]
    ) -> CommandParameters:
        named_args = {}
        if IS_CONAN_V1:
            pass
        else:
            named_args["v2_need_reference"] = True
        return self._make_common_params(
            "remove",
            workers_api.removepackage.invoke,
            recipe_attributes,
            with_explicit_name=True,
            with_pkgref=True,
            with_force=True,
            with_recipe_path=False,
            **named_args,
        )

    def _conan_create_common(
        self, args: typing.Optional[typing.List[str]] = None
    ) -> None:
        # note that this is done early, to force a focus change in any
        # configuration windows, forcing serialising changes before commands kick off
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_create_params(recipe_attributes, args),
            self,
        )

    def _conan_create(self) -> None:
        self._conan_create_common()

    def _conan_create_update(self) -> None:
        self._conan_create_common(args=["--update"])

    def _conan_install_common(
        self, args: typing.Optional[typing.List[str]] = None
    ) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_install_params(recipe_attributes, args),
            self,
        )

    def _conan_install(self) -> None:
        self._conan_install_common()

    def _conan_install_update(self) -> None:
        self._conan_install_common(args=["--update"])

    def _conan_imports(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_imports_params(recipe_attributes),
            self,
        )

    def _conan_source(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_source_params(recipe_attributes),
            self,
        )

    def _conan_build(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_build_params(recipe_attributes),
            self,
        )

    def _conan_package(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_package_params(recipe_attributes),
            self,
        )

    def _conan_export_package(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_export_package_params(recipe_attributes),
            self,
        )

    def _conan_test(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_test_package_params(recipe_attributes),
            self,
        )

    def _cancel_command(self) -> None:
        recipe_widget = self._recipe_widget
        recipe = recipe_widget.recipe  # type: ignore[attr-defined]
        recipe.context.cancel()

    def _conan_remove(self) -> None:
        recipe_widget = self._recipe_widget
        try:
            recipe_attributes = recipe_widget.get_recipe_attributes()  # type: ignore[attr-defined] # noqa: E501
        except RecipeInspectionError:
            return
        self.command_started.emit()
        recipe_widget.recipe.context.conancommand(  # type: ignore[attr-defined] # noqa: E501
            self._make_conan_remove_package_params(recipe_attributes),
            self,
        )

    def _cmake_build_common(
        self, args: typing.Optional[typing.List[str]] = None
    ) -> None:
        # TODO review
        recipe_widget = self._recipe_widget
        recipe = recipe_widget.recipe  # type: ignore[attr-defined] # noqa: E501
        params = CommandParameters(
            "cmakebuild", workers_api.cmakebuildtool.invoke
        )  # TODO: verb is wrong
        with RecipeSettingsReader.from_recipe(recipe) as settings:
            num_cores = settings.num_cpu_cores
            if num_cores.value is not None:
                params.added_environment.update(
                    {"CONAN_CPU_COUNT": str(num_cores.value)}
                )
            workflow_cwd = settings.local_workflow_cwd.resolve()
            common_subdir = settings.local_workflow_common_subdir.resolve()
            params.cwd = recipe_widget.get_working_dir(workflow_cwd, common_subdir)  # type: ignore[attr-defined] # noqa: E501
            layout_build_subdir = (
                recipe_widget.dependency_graph.root.layout_build_subdir  # type: ignore[attr-defined] # noqa: E501
            )
            if layout_build_subdir:
                params.build_folder = layout_build_subdir
            else:
                build_folder = settings.local_workflow_build_folder.resolve()
                params.build_folder = recipe_widget.resolve_expression(build_folder)  # type: ignore[attr-defined] # noqa: E501
        if args:
            params.arguments.extend(args)
        self.command_started.emit()
        recipe.context.cmakebuildcommand(params, self)

    def _cmake_build(self) -> None:
        self._cmake_build_common()

    def _cmake_build_verbose(self) -> None:
        self._cmake_build_common(args=["verbose"])

    def _cmake_remove_cache(self) -> None:
        # TODO: review
        recipe_widget = self._recipe_widget
        recipe = recipe_widget.recipe  # type: ignore[attr-defined]
        params = CommandParameters(
            "cmakeremovecache", workers_api.deletecmakecache.invoke
        )  # TODO: verb is wrong
        with RecipeSettingsReader.from_recipe(recipe) as settings:
            workflow_cwd = settings.local_workflow_cwd.resolve()
            common_subdir = settings.local_workflow_common_subdir.resolve()
            params.cwd = recipe_widget.get_working_dir(workflow_cwd, common_subdir)  # type: ignore[attr-defined] # noqa: E501
            layout_build_subdir = (
                recipe_widget.dependency_graph.root.layout_build_subdir  # type: ignore[attr-defined] # noqa: E501
            )
            if layout_build_subdir:
                params.build_folder = layout_build_subdir
            else:
                build_folder = settings.local_workflow_build_folder.resolve()
                params.build_folder = recipe_widget.resolve_expression(build_folder)  # type: ignore[attr-defined] # noqa: E501
        self.command_started.emit()
        recipe.context.cmakebuildcommand(params, self)

    def _generate_command_tooltip(self, params: CommandParameters) -> str:
        tooltip = StringIO()
        tooltip.write(f"<p style='white-space:pre'><b>{params}</b></p>\n")
        if params.cwd:
            tooltip.write("<p style='white-space:pre'>Working directory<br>")
            tooltip.write(f" <em>{params.cwd}</em></p>\n")
        if params.added_environment:
            tooltip.write("<p style='white-space:pre'>Environment<br>")
            for key, value in params.added_environment.items():
                tooltip.write(f" {key}={value}<br>")
            tooltip.write("</p>")
        return tooltip.getvalue()
