#!/usr/bin/env python3

"""
Application settings utilities
"""

import json
import pathlib
import typing

from qtpy import QtCore, QtGui, QtWidgets

import cruiz.globals

from cruiz.settings.managers.namedlocalcache import NamedLocalCacheSettingsReader

from cruiz.pyside6.preferences import Ui_PreferencesDialog

from cruiz.settings.managers.generalpreferences import (
    GeneralSettings,
    GeneralSettingsReader,
    GeneralSettingsWriter,
)
from cruiz.settings.managers.fontpreferences import (
    FontUsage,
    FontSettings,
    FontSettingsReader,
    FontSettingsWriter,
)
from cruiz.settings.managers.conanpreferences import (
    ConanSettings,
    ConanSettingsReader,
    ConanSettingsWriter,
)
from cruiz.settings.managers.localcachepreferences import (
    LocalCacheSettings,
    LocalCacheSettingsReader,
    LocalCacheSettingsWriter,
)
from cruiz.settings.managers.namedlocalcache import (
    AllNamedLocalCacheSettingsReader,
    NamedLocalCacheDeleter,
)
from cruiz.settings.managers.graphvizpreferences import (
    GraphVizSettings,
    GraphVizSettingsReader,
    GraphVizSettingsWriter,
)
from cruiz.settings.managers.cmakepreferences import (
    CMakeSettings,
    CMakeSettingsReader,
    CMakeSettingsWriter,
)
from cruiz.settings.managers.ninjapreferences import (
    NinjaSettings,
    NinjaSettingsReader,
    NinjaSettingsWriter,
)
from cruiz.settings.managers.compilercachepreferences import (
    CompilerCacheSettings,
    CompilerCacheSettingsReader,
    CompilerCacheSettingsWriter,
)
from cruiz.settings.managers.recentrecipes import (
    RecentRecipeSettingsReader,
    RecentRecipeSettingsDeleter,
)
from cruiz.settings.managers.recipe import (
    RecipeSettingsReader,
    RecipeSettingsWriter,
    RecipeSettings,
    RecipeSettingsDeleter,
)
from cruiz.settings.managers.recentconanconfigs import (
    RecentConanConfigSettingsReader,
    RecentConanConfigSettingsDeleter,
)
from cruiz.settings.managers.recentconanremotes import (
    RecentConanRemotesSettingsReader,
    RecentConanRemotesSettingsDeleter,
)
from cruiz.settings.managers.shortcuts import (
    ShortcutSettings,
    ShortcutSettingsReader,
    ShortcutSettingsWriter,
)
from cruiz.settings.managers.cleansettings import sanitise_settings
from cruiz.settings.managers.restoredefaults import factory_reset

from cruiz.settings.models.recentconanremotesmodel import RecentConanRemotesModel
from cruiz.settings.models.recentconanconfigmodel import RecentConanConfigModel
from cruiz.settings.models.recipesmodel import RecipesModel

from cruiz.widgets.util import BlockSignals, search_for_file_options

from cruiz.constants import DEFAULT_CACHE_NAME


class PreferencesDialog(QtWidgets.QDialog):
    """
    Dialog representing the preferences.
    """

    modified = QtCore.Signal()
    preferences_updated = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self._ui = Ui_PreferencesDialog()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        # -- signals
        self.modified.connect(self._modification_applied)
        self.preferences_updated.connect(
            qApp.on_preferences_updated  # type: ignore  # noqa: F821
        )
        cruiz.globals.get_main_window().theme_changed.connect(
            self._refresh_shortcut_icons
        )
        # -- toolbox
        self._ui.prefs_toolbox.currentChanged.connect(self._current_load_defaults)
        self._import_prefs = QtWidgets.QPushButton("Import...")
        self._export_prefs = QtWidgets.QPushButton("Export...")
        self._clean_prefs = QtWidgets.QPushButton("Clean...")
        self._restore_default_prefs = QtWidgets.QPushButton("Restore defaults")
        self._setup_buttons()
        self._setup_general_toolbox()
        self._setup_font_toolbox()
        self._setup_conan_toolbox()
        self._setup_localcache_toolbox()
        self._setup_graphviz_toolbox()
        self._setup_cmake_toolbox()
        self._setup_compilercache_toolbox()
        self._setup_shortcuts_toolbox()
        self._setup_recipes_toolbox()
        self._setup_recentconfigs_toolbox()
        self._setup_recentremotes_toolbox()
        # -- load initial toolbox settings
        self._current_load_defaults(self._ui.prefs_toolbox.currentIndex())

    def _any_modifications(self) -> bool:
        return (
            not self._prefs_general.empty(GeneralSettingsReader())
            or not self._prefs_font[FontUsage.UI].empty(
                FontSettingsReader(FontUsage.UI)
            )
            or not self._prefs_font[FontUsage.OUTPUT].empty(
                FontSettingsReader(FontUsage.OUTPUT)
            )
            or not self._prefs_conan.empty(ConanSettingsReader())
            or not self._prefs_localcache.empty(LocalCacheSettingsReader())
            or not self._prefs_graphviz.empty(GraphVizSettingsReader())
            or not self._prefs_cmake.empty(CMakeSettingsReader())
            or not self._prefs_ninja.empty(NinjaSettingsReader())
            or not self._prefs_compilercache.empty(CompilerCacheSettingsReader())
            or not self._prefs_shortcuts.empty(ShortcutSettingsReader())
        )

    def _save(self) -> None:
        GeneralSettingsWriter().sync(self._prefs_general)
        FontSettingsWriter(FontUsage.UI).sync(self._prefs_font[FontUsage.UI])
        FontSettingsWriter(FontUsage.OUTPUT).sync(self._prefs_font[FontUsage.OUTPUT])
        ConanSettingsWriter().sync(self._prefs_conan)
        LocalCacheSettingsWriter().sync(self._prefs_localcache)
        GraphVizSettingsWriter().sync(self._prefs_graphviz)
        CMakeSettingsWriter().sync(self._prefs_cmake)
        NinjaSettingsWriter().sync(self._prefs_ninja)
        CompilerCacheSettingsWriter().sync(self._prefs_compilercache)
        ShortcutSettingsWriter().sync(self._prefs_shortcuts)
        self.modified.emit()
        self._current_load_defaults(self._ui.prefs_toolbox.currentIndex())
        self.preferences_updated.emit()

    def _modification_applied(self) -> None:
        enabled = self._any_modifications()
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        ).setEnabled(enabled)
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(enabled)

    def _setup_buttons(self) -> None:
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        ).clicked.connect(self._save)
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).clicked.connect(self._save)
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).clicked.connect(self.accept)
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Apply
        ).setEnabled(False)
        self._ui.prefs_buttons.button(
            QtWidgets.QDialogButtonBox.StandardButton.Ok
        ).setEnabled(False)
        self._ui.prefs_buttons.addButton(
            self._import_prefs, QtWidgets.QDialogButtonBox.ActionRole
        )
        self._ui.prefs_buttons.addButton(
            self._export_prefs, QtWidgets.QDialogButtonBox.ActionRole
        )
        self._ui.prefs_buttons.addButton(
            self._clean_prefs, QtWidgets.QDialogButtonBox.ActionRole
        )
        self._ui.prefs_buttons.addButton(
            self._restore_default_prefs, QtWidgets.QDialogButtonBox.ActionRole
        )
        self._import_prefs.clicked.connect(self._import_presets)
        self._export_prefs.clicked.connect(self._export_presets)
        self._clean_prefs.clicked.connect(self._clean_preferences)
        self._restore_default_prefs.clicked.connect(self._restore_defaults)

    def _setup_general_toolbox(self) -> None:
        self._prefs_general = GeneralSettings()
        self._ui.prefs_general_clearpanes.stateChanged.connect(
            self._general_clearplanes
        )
        self._ui.prefs_general_combine_panes.stateChanged.connect(
            self._general_combinepanes
        )
        self._ui.prefs_general_usebatching.stateChanged.connect(
            self._general_usebatching
        )
        self._ui.prefs_general_enable_wallclock.stateChanged.connect(
            self._general_wallclock
        )
        self._ui.prefs_general_enable_compact.stateChanged.connect(
            self._general_compactlook
        )
        dir_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        open_recipedir_action = QtGui.QAction(dir_icon, "", self)
        open_recipedir_action.triggered.connect(self._general_open_recipedir)
        self._ui.prefs_general_default_recipe_dir.addAction(
            open_recipedir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.prefs_general_default_recipe_dir.textChanged.connect(
            self._general_recipedir
        )
        self._ui.prefs_general_busy_colour.clicked.connect(self._general_busyiconcolour)
        self._ui.prefs_general_found_text_background_colour.clicked.connect(
            self._general_foundtextbgroundcolour
        )
        open_recipe_in_editor_action = QtGui.QAction(dir_icon, "", self)
        open_recipe_in_editor_action.triggered.connect(self._general_open_recipe_editor)
        self._ui.prefs_general_recipe_editor.addAction(
            open_recipe_in_editor_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.prefs_general_recipe_editor.textChanged.connect(
            self._general_recipe_editor
        )
        self._ui.prefs_general_new_recipe_load.stateChanged.connect(
            self._general_newrecipeload
        )  # TODO: this has no place in the new UI

    def _setup_font_toolbox(self) -> None:
        self._prefs_font = {
            FontUsage.UI: FontSettings(),
            FontUsage.OUTPUT: FontSettings(),
        }
        self._ui.prefs_font_ui_change.clicked.connect(self._font_change_ui)
        self._ui.prefs_font_ui_reset.clicked.connect(self._font_reset_ui)
        self._ui.prefs_font_output_change.clicked.connect(self._font_change_output)
        self._ui.prefs_font_output_reset.clicked.connect(self._font_reset_output)

    def _setup_conan_toolbox(self) -> None:
        self._prefs_conan = ConanSettings()
        self._ui.prefs_conan_log_level.currentTextChanged.connect(
            self._conan_change_log_level
        )
        self._ui.prefs_conan_version_list_path_segment.textChanged.connect(
            self._conan_version_list_path_segment_changed
        )

    def _setup_localcache_toolbox(self) -> None:
        self._prefs_localcache = LocalCacheSettings()
        self._ui.prefs_localcache_config_to_install.textChanged.connect(
            self._localcache_install_path_changed
        )
        self._ui.prefs_localcache_config_git_branch.textChanged.connect(
            self._localcache_install_branch_changed
        )
        self._ui.prefs_localcache_forget_cache.currentTextChanged.connect(
            self._localcache_change_forget_cache
        )
        self._ui.prefs_localcache_do_forget.clicked.connect(
            self._localcache_forget_cache
        )

    def _setup_graphviz_toolbox(self) -> None:
        self._prefs_graphviz = GraphVizSettings()
        self._ui.prefs_graphviz_bin_directory.textChanged.connect(
            self._graphviz_bin_directory_changed
        )
        open_graphviz_bindir_action = QtGui.QAction(
            self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon), "", self
        )
        open_graphviz_bindir_action.triggered.connect(self._graphviz_open_bindir)
        self._ui.prefs_graphviz_bin_directory.addAction(
            open_graphviz_bindir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )

    def _setup_cmake_toolbox(self) -> None:
        self._prefs_cmake = CMakeSettings()
        self._prefs_ninja = NinjaSettings()
        self._ui.prefs_cmake_cmake_bin_directory.textChanged.connect(
            self._cmake_bin_directory_changed
        )
        dir_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        open_cmake_bindir_action = QtGui.QAction(dir_icon, "", self)
        open_cmake_bindir_action.triggered.connect(self._cmake_open_bindir)
        self._ui.prefs_cmake_cmake_bin_directory.addAction(
            open_cmake_bindir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.prefs_cmake_ninja_bin_directory.textChanged.connect(
            self._ninja_bin_directory_changed
        )
        open_ninja_bindir_action = QtGui.QAction(dir_icon, "", self)
        open_ninja_bindir_action.triggered.connect(self._ninja_open_bindir)
        self._ui.prefs_cmake_ninja_bin_directory.addAction(
            open_ninja_bindir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )

    def _setup_compilercache_toolbox(self) -> None:
        self._prefs_compilercache = CompilerCacheSettings()
        self._ui.prefs_compilercache_default.currentTextChanged.connect(
            self._compilercache_default_changed
        )
        self._ui.prefs_compilercache_ccache_location.textChanged.connect(
            self._compilercache_ccache_bin_directory_changed
        )
        dir_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        open_ccache_bindir_action = QtGui.QAction(dir_icon, "", self)
        open_ccache_bindir_action.triggered.connect(
            self._compilercache_open_ccache_bindir
        )
        self._ui.prefs_compilercache_ccache_location.addAction(
            open_ccache_bindir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.prefs_compilercache_sccache_location.textChanged.connect(
            self._compilercache_sccache_bin_directory_changed
        )
        open_scache_bindir_action = QtGui.QAction(dir_icon, "", self)
        open_scache_bindir_action.triggered.connect(
            self._compilercache_open_sccache_bindir
        )
        self._ui.prefs_compilercache_sccache_location.addAction(
            open_scache_bindir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.prefs_compilercache_buildcache_location.textChanged.connect(
            self._compilercache_buildcache_bin_directory_changed
        )
        open_buildcache_bindir_action = QtGui.QAction(dir_icon, "", self)
        open_buildcache_bindir_action.triggered.connect(
            self._compilercache_open_buildcache_bindir
        )
        self._ui.prefs_compilercache_buildcache_location.addAction(
            open_buildcache_bindir_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )

    def _setup_shortcuts_toolbox(self) -> None:
        self._prefs_shortcuts = ShortcutSettings()
        self._ui.prefs_shortcuts_create_edit.textChanged.connect(
            self._shortcuts_change_create
        )
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            self._ui.prefs_shortcuts_imports_edit.textChanged.connect(
                self._shortcuts_change_imports
            )
        else:
            self._ui.prefs_shortcuts_imports_label.hide()
            self._ui.prefs_shortcuts_imports_edit.hide()
        self._ui.prefs_shortcuts_install_edit.textChanged.connect(
            self._shortcuts_change_install
        )
        self._ui.prefs_shortcuts_installupdates_edit.textChanged.connect(
            self._shortcuts_change_installupdates
        )
        self._ui.prefs_shortcuts_source_edit.textChanged.connect(
            self._shortcuts_change_source
        )
        self._ui.prefs_shortcuts_build_edit.textChanged.connect(
            self._shortcuts_change_build
        )
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            self._ui.prefs_shortcuts_package_edit.textChanged.connect(
                self._shortcuts_change_package
            )
        else:
            self._ui.prefs_shortcuts_package_label.hide()
            self._ui.prefs_shortcuts_package_edit.hide()
        self._ui.prefs_shortcuts_exportpackage_edit.textChanged.connect(
            self._shortcuts_change_exportpkg
        )
        self._ui.prefs_shortcuts_test_edit.textChanged.connect(
            self._shortcuts_change_test
        )
        self._ui.prefs_shortcuts_remove_edit.textChanged.connect(
            self._shortcuts_change_remove
        )
        self._ui.prefs_shortcuts_cancel_edit.textChanged.connect(
            self._shortcuts_change_cancel
        )
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            self._ui.prefs_shortcuts_cmakebuildtool_edit.textChanged.connect(
                self._shortcuts_change_cmakebuildtool
            )
            self._ui.prefs_shortcuts_cmakebuildtoolverbose_edit.textChanged.connect(
                self._shortcuts_change_cmakebuildtoolverbose
            )
            self._ui.prefs_shortcuts_deletecmakecache_edit.textChanged.connect(
                self._shortcuts_change_deletecmakecache
            )
        else:
            self._ui.prefs_shortcuts_cmakebuildtool_label.hide()
            self._ui.prefs_shortcuts_cmakebuildtool_edit.hide()
            self._ui.prefs_shortcuts_cmakebuildtoolverbose_label.hide()
            self._ui.prefs_shortcuts_cmakebuildtoolverbose_edit.hide()
            self._ui.prefs_shortcuts_deletecmakecache_label.hide()
            self._ui.prefs_shortcuts_deletecmakecache_edit.hide()
        self._refresh_shortcut_icons()

    def _setup_recipes_toolbox(self) -> None:
        self._prefs_recipes_model = RecipesModel()
        self._ui.prefs_recipes_table.setModel(self._prefs_recipes_model)
        self._ui.prefs_recipes_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )
        self._ui.prefs_recipes_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.ResizeToContents
        )
        self._ui.prefs_recipes_table.addAction(self._ui.actionForget_recipe)
        self._ui.prefs_recipes_table.customContextMenuRequested.connect(
            self._recipes_context_menu
        )

    def _setup_recentconfigs_toolbox(self) -> None:
        self._prefs_recentconfigs_model = RecentConanConfigModel()
        self._ui.prefs_recentconfigs_list.setModel(self._prefs_recentconfigs_model)
        self._ui.prefs_recentconfigs_list.addAction(self._ui.actionForget_config)
        self._ui.prefs_recentconfigs_list.customContextMenuRequested.connect(
            self._recentconfigs_context_menu
        )

    def _setup_recentremotes_toolbox(self) -> None:
        self._prefs_recentremotes_model = RecentConanRemotesModel()
        self._ui.prefs_recentremotes_list.setModel(self._prefs_recentremotes_model)
        self._ui.prefs_recentremotes_list.addAction(self._ui.actionForget_remote)
        self._ui.prefs_recentremotes_list.customContextMenuRequested.connect(
            self._recentremotes_context_menu
        )

    def _current_load_defaults(self, index: int) -> None:
        widget = self._ui.prefs_toolbox.widget(index)
        name = widget.objectName()
        if name == "prefs_general":
            self._general_load_defaults()
        elif name == "prefs_fonts":
            self._font_load_defaults()
        elif name == "prefs_conan":
            self._conan_load_defaults()
        elif name == "prefs_localcache":
            self._localcache_load_defaults()
        elif name == "prefs_graphviz":
            self._graphviz_load_defaults()
        elif name == "prefs_cmake":
            self._cmake_load_defaults()
        elif name == "prefs_compilercache":
            self._compilercache_load_defaults()
        elif name == "prefs_shortcuts":
            self._shortcuts_load_defaults()
        elif name == "prefs_recipes":
            self._recipes_load_defaults()
        elif name == "prefs_recentconfigs":
            self._recentconfigs_load_defaults()
        elif name == "prefs_recentremotes":
            self._recentremotes_load_defaults()
        else:
            raise RuntimeError(f"Unknown toolbox widget with name '{name}")

    def reject(self) -> None:
        if self._any_modifications():
            response = QtWidgets.QMessageBox.question(
                self,
                "Unsaved preferences",
                "Modifications are unsaved. Do you want to discard them?",
            )
            if response == QtWidgets.QMessageBox.No:
                return
        super().reject()

    # -- general --

    def _update_busy_icon_colour(self, colour: QtGui.QColor) -> None:
        self._ui.prefs_general_busy_colour.setStyleSheet(
            "background-color: " f"rgb({colour.red()},{colour.green()},{colour.blue()})"
        )

    def _update_found_text_background_colour(self, colour: QtGui.QColor) -> None:
        self._ui.prefs_general_found_text_background_colour.setStyleSheet(
            "background-color: " f"rgb({colour.red()},{colour.green()},{colour.blue()})"
        )

    def _general_load_defaults(self) -> None:
        with GeneralSettingsReader() as settings:
            with BlockSignals(self._ui.prefs_general_clearpanes) as blocked_widget:
                blocked_widget.setChecked(settings.clear_panes.resolve())
            with BlockSignals(self._ui.prefs_general_combine_panes) as blocked_widget:
                blocked_widget.setChecked(settings.combine_panes.resolve())
            with BlockSignals(self._ui.prefs_general_usebatching) as blocked_widget:
                blocked_widget.setChecked(settings.use_stdout_batching.resolve())
            with BlockSignals(
                self._ui.prefs_general_enable_wallclock
            ) as blocked_widget:
                blocked_widget.setChecked(settings.enable_command_timing.resolve())
            with BlockSignals(self._ui.prefs_general_enable_compact) as blocked_widget:
                blocked_widget.setChecked(settings.use_compact_look.resolve())
            with BlockSignals(
                self._ui.prefs_general_default_recipe_dir
            ) as blocked_widget:
                blocked_widget.setText(
                    settings.default_recipe_directory.resolve() or ""
                )
            with BlockSignals(self._ui.prefs_general_busy_colour):
                colour = settings.busy_icon_colour.resolve()
                self._update_busy_icon_colour(colour)
            with BlockSignals(self._ui.prefs_general_found_text_background_colour):
                colour = settings.found_text_background_colour.resolve()
                self._update_found_text_background_colour(colour)
            with BlockSignals(self._ui.prefs_general_recipe_editor) as blocked_widget:
                blocked_widget.setText(settings.default_recipe_editor.resolve() or "")
            # Note: the following is not part of the new UI
            with BlockSignals(self._ui.prefs_general_new_recipe_load) as blocked_widget:
                blocked_widget.setChecked(
                    settings.new_recipe_loading_behaviour.resolve()
                )

    def _general_clearplanes(self, state: int) -> None:
        self._prefs_general.clear_panes = (
            QtCore.Qt.CheckState(state) == QtCore.Qt.Checked
        )
        self.modified.emit()

    def _general_combinepanes(self, state: int) -> None:
        self._prefs_general.combine_panes = (
            QtCore.Qt.CheckState(state) == QtCore.Qt.Checked
        )
        self.modified.emit()
        self._requires_restart()

    def _general_usebatching(self, state: int) -> None:
        self._prefs_general.use_stdout_batching = (
            QtCore.Qt.CheckState(state) == QtCore.Qt.Checked
        )
        self.modified.emit()
        self._requires_restart()

    def _general_wallclock(self, state: int) -> None:
        self._prefs_general.enable_command_timing = (
            QtCore.Qt.CheckState(state) == QtCore.Qt.Checked
        )
        self.modified.emit()

    def _general_compactlook(self, state: int) -> None:
        self._prefs_general.use_compact_look = (
            QtCore.Qt.CheckState(state) == QtCore.Qt.Checked
        )
        self.modified.emit()

    def _general_open_recipedir(self) -> None:
        with GeneralSettingsReader() as settings:
            last_dir = settings.default_recipe_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select default recipe directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_general_default_recipe_dir.setText(new_dir)

    def _general_recipedir(self, text: str) -> None:
        self._prefs_general.default_recipe_directory = text or None  # type: ignore
        self.modified.emit()

    def _general_busyiconcolour(self) -> None:
        with GeneralSettingsReader() as settings:
            busy_color = settings.busy_icon_colour.resolve()
        dialog = QtWidgets.QColorDialog(busy_color, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_color = dialog.currentColor()
            self._update_busy_icon_colour(new_color)
            self._prefs_general.busy_icon_colour = new_color  # type: ignore[assignment]
            self.modified.emit()

    def _general_foundtextbgroundcolour(self) -> None:
        with GeneralSettingsReader() as settings:
            color = settings.found_text_background_colour.resolve()
        dialog = QtWidgets.QColorDialog(color, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_color = dialog.currentColor()
            self._update_found_text_background_colour(new_color)
            self._prefs_general.found_text_background_colour = (
                new_color  # type: ignore[assignment]
            )
            self.modified.emit()

    def _general_open_recipe_editor(self) -> None:
        with GeneralSettingsReader() as settings:
            last_dir = settings.default_recipe_editor.resolve()
        new_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            caption="Select default recipe editor",
            dir=last_dir,
            options=search_for_file_options(),
        )
        if new_path:
            self._ui.prefs_general_recipe_editor.setText(new_path)

    def _general_recipe_editor(self, text: str) -> None:
        self._prefs_general.default_recipe_editor = text or None  # type: ignore
        self.modified.emit()

    def _general_newrecipeload(self, state: int) -> None:
        self._prefs_general.new_recipe_loading_behaviour = (
            QtCore.Qt.CheckState(state) == QtCore.Qt.Checked
        )
        self.modified.emit()

    # -- font --
    @staticmethod
    def _font_from_details(
        details: typing.Tuple[typing.Optional[str], typing.Optional[int]]
    ) -> typing.Optional[QtGui.QFont]:
        font = QtGui.QFont(*details) if details[0] else None  # type: ignore
        return font

    @staticmethod
    def _font_description(font: QtGui.QFont) -> str:
        return f"{font.family()} at size {font.pointSize()}"

    def _font_set_ui_preview(self, font: QtGui.QFont) -> None:
        self._ui.prefs_font_ui_label.setText(PreferencesDialog._font_description(font))
        self._ui.prefs_font_ui_preview.setFont(font)

    def _font_set_output_preview(self, font: QtGui.QFont) -> None:
        self._ui.prefs_font_output_label.setText(
            PreferencesDialog._font_description(font)
        )
        self._ui.prefs_font_output_preview.setFont(font)

    def _font_load_defaults(self) -> None:
        with FontSettingsReader(FontUsage.UI) as settings:
            font = (
                PreferencesDialog._font_from_details(
                    (settings.name.resolve(), settings.size.resolve())
                )
                or qApp.default_font  # type: ignore  # noqa: F821
            )
        self._font_set_ui_preview(font)

        with FontSettingsReader(FontUsage.OUTPUT) as settings:
            font = PreferencesDialog._font_from_details(
                (settings.name.resolve(), settings.size.resolve())
            ) or QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
        self._font_set_output_preview(font)

    def _font_change(self, usage: FontUsage, default_font: QtGui.QFont) -> None:
        with FontSettingsReader(usage) as settings:
            desired_font = (
                PreferencesDialog._font_from_details(
                    (settings.name.resolve(), settings.size.resolve())
                )
                or default_font
            )
        is_ok, font = (
            QtWidgets.QFontDialog.getFont(desired_font, self)
            if desired_font
            else QtWidgets.QFontDialog.getFont(self)
        )
        if is_ok:
            """
            with FontWriteAccess(usage) as fontsettings:
                fontsettings.name = font.family()
                fontsettings.size = font.pointSize()
                self._font_load_defaults()
            """
            assert isinstance(font, QtGui.QFont)
            self._prefs_font[usage].name = font.family()  # type: ignore
            self._prefs_font[usage].size = font.pointSize()  # type: ignore
            if usage == FontUsage.UI:
                self._font_set_ui_preview(font)
            elif usage == FontUsage.OUTPUT:
                self._font_set_output_preview(font)
            self.modified.emit()

    def _font_change_ui(self) -> None:
        self._font_change(FontUsage.UI, qApp.default_font)  # type: ignore # noqa: F821

    def _font_change_output(self) -> None:
        self._font_change(
            FontUsage.OUTPUT,
            QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont),
        )

    def _font_reset(self, usage: FontUsage) -> None:
        """
        with FontWriteAccess(usage) as fontsettings:
            del fontsettings.name
            del fontsettings.size
            self._font_load_defaults()
        """
        self._prefs_font[usage].name = None  # type: ignore
        self._prefs_font[usage].size = None  # type: ignore
        if usage == FontUsage.UI:
            self._font_set_ui_preview(qApp.default_font)  # type: ignore # noqa: F821
        elif usage == FontUsage.OUTPUT:
            self._font_set_output_preview(
                QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont)
            )
        self.modified.emit()

    def _font_reset_ui(self) -> None:
        self._font_reset(FontUsage.UI)

    def _font_reset_output(self) -> None:
        self._font_reset(FontUsage.OUTPUT)

    # -- conan --
    def _conan_load_defaults(self) -> None:
        with ConanSettingsReader() as settings:
            log_level = settings.log_level.resolve()
            conandata_version_yaml_pathsegment = (
                settings.conandata_version_yaml_pathsegment.resolve()
            )
        with BlockSignals(self._ui.prefs_conan_log_level) as blocked_widget:
            blocked_widget.setCurrentText(log_level)
        with BlockSignals(
            self._ui.prefs_conan_version_list_path_segment
        ) as blocked_widget:
            blocked_widget.setText(conandata_version_yaml_pathsegment)

    def _conan_change_log_level(self, text: str) -> None:
        self._prefs_conan.log_level = text  # type: ignore
        self.modified.emit()

    def _conan_version_list_path_segment_changed(self, text: str) -> None:
        value = text or None
        self._prefs_conan.conandata_version_yaml_pathsegment = value  # type: ignore
        self.modified.emit()

    # -- local cache --
    def _localcache_load_defaults(self) -> None:
        with LocalCacheSettingsReader() as settings:
            install_path = settings.new_configuration_install.resolve()
            git_branch = settings.new_configuration_git_branch.resolve()
        with BlockSignals(
            self._ui.prefs_localcache_config_to_install
        ) as blocked_widget:
            blocked_widget.setText(install_path)
        with BlockSignals(
            self._ui.prefs_localcache_config_git_branch
        ) as blocked_widget:
            blocked_widget.setText(git_branch)
        with BlockSignals(self._ui.prefs_localcache_forget_cache) as blocked_widget:
            blocked_widget.clear()
            with AllNamedLocalCacheSettingsReader() as names:
                blocked_widget.addItems(names)
        self._localcache_change_forget_cache(
            self._ui.prefs_localcache_forget_cache.currentText()
        )

    def _localcache_install_path_changed(self, text: str) -> None:
        self._prefs_localcache.new_configuration_install = text or None  # type: ignore
        self.modified.emit()

    def _localcache_install_branch_changed(self, text: str) -> None:
        value = text or None
        self._prefs_localcache.new_configuration_git_branch = value  # type: ignore
        self.modified.emit()

    def _localcache_change_forget_cache(self, text: str) -> None:
        with NamedLocalCacheSettingsReader(text) as settings:
            uuids = settings.recipe_uuids
        self._ui.prefs_localcache_do_forget.setEnabled(
            not uuids and text != DEFAULT_CACHE_NAME
        )

    def _localcache_forget_cache(self) -> None:
        NamedLocalCacheDeleter().delete(
            self._ui.prefs_localcache_forget_cache.currentText()
        )

    # -- graphviz --
    def _graphviz_load_defaults(self) -> None:
        with GraphVizSettingsReader() as settings:
            bin_path = settings.bin_directory.resolve()
        with BlockSignals(self._ui.prefs_graphviz_bin_directory) as blocked_widget:
            blocked_widget.setText(bin_path)

    def _graphviz_bin_directory_changed(self, text: str) -> None:
        self._prefs_graphviz.bin_directory = text or None  # type: ignore
        self.modified.emit()

    def _graphviz_open_bindir(self) -> None:
        with GraphVizSettingsReader() as settings:
            last_dir = settings.bin_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select GraphViz bin directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_graphviz_bin_directory.setText(new_dir)

    # -- CMake & Ninja --
    def _cmake_load_defaults(self) -> None:
        with CMakeSettingsReader() as settings:
            cmake_bin_path = settings.bin_directory.resolve()
        with BlockSignals(self._ui.prefs_cmake_cmake_bin_directory) as blocked_widget:
            blocked_widget.setText(cmake_bin_path)
        with NinjaSettingsReader() as settings:
            ninja_bin_path = settings.bin_directory.resolve()
        with BlockSignals(self._ui.prefs_cmake_ninja_bin_directory) as blocked_widget:
            blocked_widget.setText(ninja_bin_path)

    def _cmake_bin_directory_changed(self, text: str) -> None:
        self._prefs_cmake.bin_directory = text or None  # type: ignore
        self.modified.emit()

    def _cmake_open_bindir(self) -> None:
        with CMakeSettingsReader() as settings:
            last_dir = settings.bin_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select CMake bin directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_cmake_cmake_bin_directory.setText(new_dir)

    def _ninja_bin_directory_changed(self, text: str) -> None:
        self._prefs_ninja.bin_directory = text or None  # type: ignore
        self.modified.emit()

    def _ninja_open_bindir(self) -> None:
        with NinjaSettingsReader() as settings:
            last_dir = settings.bin_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select Ninja bin directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_cmake_ninja_bin_directory.setText(new_dir)

    # -- Compiler cache --
    def _compilercache_load_defaults(self) -> None:
        with CompilerCacheSettingsReader() as settings:
            compilercache_default = settings.default.resolve()
            ccache_bin_dir = settings.ccache_bin_directory.resolve()
            sccache_bin_dir = settings.sccache_bin_directory.resolve()
            buildcache_bin_dir = settings.buildcache_bin_directory.resolve()
        with BlockSignals(self._ui.prefs_compilercache_default) as blocked_widget:
            blocked_widget.setCurrentText(compilercache_default)
        with BlockSignals(
            self._ui.prefs_compilercache_ccache_location
        ) as blocked_widget:
            blocked_widget.setText(ccache_bin_dir)
        with BlockSignals(
            self._ui.prefs_compilercache_sccache_location
        ) as blocked_widget:
            blocked_widget.setText(sccache_bin_dir)
        with BlockSignals(
            self._ui.prefs_compilercache_buildcache_location
        ) as blocked_widget:
            blocked_widget.setText(buildcache_bin_dir)

    def _compilercache_default_changed(self, text: str) -> None:
        self._prefs_compilercache.default = text  # type: ignore
        self.modified.emit()

    def _compilercache_ccache_bin_directory_changed(self, text: str) -> None:
        self._prefs_compilercache.ccache_bin_directory = text or None  # type: ignore
        self.modified.emit()

    def _compilercache_open_ccache_bindir(self) -> None:
        with CompilerCacheSettingsReader() as settings:
            last_dir = settings.ccache_bin_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select ccache bin directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_compilercache_ccache_location.setText(new_dir)

    def _compilercache_sccache_bin_directory_changed(self, text: str) -> None:
        self._prefs_compilercache.sccache_bin_directory = text or None  # type: ignore
        self.modified.emit()

    def _compilercache_open_sccache_bindir(self) -> None:
        with CompilerCacheSettingsReader() as settings:
            last_dir = settings.sccache_bin_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select sccache bin directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_compilercache_sccache_location.setText(new_dir)

    def _compilercache_buildcache_bin_directory_changed(self, text: str) -> None:
        value = text or None
        self._prefs_compilercache.buildcache_bin_directory = value  # type: ignore
        self.modified.emit()

    def _compilercache_open_buildcache_bindir(self) -> None:
        with CompilerCacheSettingsReader() as settings:
            last_dir = settings.buildcache_bin_directory.resolve()
        new_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            caption="Select buildcache bin directory",
            dir=last_dir,
        )
        if new_dir:
            self._ui.prefs_compilercache_buildcache_location.setText(new_dir)

    # -- Shortcuts --
    def _shortcuts_load_defaults(self) -> None:
        with ShortcutSettingsReader() as settings:
            conan_create = settings.conan_create
            conan_create_updates = settings.conan_create_updates
            conan_imports = settings.conan_imports
            conan_install = settings.conan_install
            conan_install_updates = settings.conan_install_updates
            conan_source = settings.conan_source
            conan_build = settings.conan_build
            conan_package = settings.conan_package
            conan_exportpkg = settings.conan_export_package
            conan_test = settings.conan_test_package
            conan_remove = settings.conan_remove_package
            cancel = settings.cancel
            cmake_build_tool = settings.cmake_build_tool
            cmake_build_tool_verbose = settings.cmake_build_tool_verbose
            remove_cmakecache = settings.delete_cmake_cache

        with BlockSignals(self._ui.prefs_shortcuts_create_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_create.fallback)
            blocked_widget.setText(conan_create.value or "")
        with BlockSignals(
            self._ui.prefs_shortcuts_createupdates_edit
        ) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_create_updates.fallback)
            blocked_widget.setText(conan_create_updates.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_imports_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_imports.fallback)
            blocked_widget.setText(conan_imports.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_install_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_install.fallback)
            blocked_widget.setText(conan_install.value or "")
        with BlockSignals(
            self._ui.prefs_shortcuts_installupdates_edit
        ) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_install_updates.fallback)
            blocked_widget.setText(conan_install_updates.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_source_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_source.fallback)
            blocked_widget.setText(conan_source.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_build_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_build.fallback)
            blocked_widget.setText(conan_build.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_package_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_package.fallback)
            blocked_widget.setText(conan_package.value or "")
        with BlockSignals(
            self._ui.prefs_shortcuts_exportpackage_edit
        ) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_exportpkg.fallback)
            blocked_widget.setText(conan_exportpkg.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_test_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_test.fallback)
            blocked_widget.setText(conan_test.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_remove_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(conan_remove.fallback)
            blocked_widget.setText(conan_remove.value or "")
        with BlockSignals(self._ui.prefs_shortcuts_cancel_edit) as blocked_widget:
            blocked_widget.setPlaceholderText(cancel.fallback)
            blocked_widget.setText(cancel.value or "")
        with BlockSignals(
            self._ui.prefs_shortcuts_cmakebuildtool_edit
        ) as blocked_widget:
            blocked_widget.setPlaceholderText(cmake_build_tool.fallback)
            blocked_widget.setText(cmake_build_tool.value or "")
        with BlockSignals(
            self._ui.prefs_shortcuts_cmakebuildtoolverbose_edit
        ) as blocked_widget:
            blocked_widget.setPlaceholderText(cmake_build_tool_verbose.fallback)
            blocked_widget.setText(cmake_build_tool_verbose.value or "")
        with BlockSignals(
            self._ui.prefs_shortcuts_deletecmakecache_edit
        ) as blocked_widget:
            blocked_widget.setPlaceholderText(remove_cmakecache.fallback)
            blocked_widget.setText(remove_cmakecache.value or "")

    def _shortcuts_change_create(self, text: str) -> None:
        self._prefs_shortcuts.conan_create = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_imports(self, text: str) -> None:
        self._prefs_shortcuts.conan_imports = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_install(self, text: str) -> None:
        self._prefs_shortcuts.conan_install = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_installupdates(self, text: str) -> None:
        self._prefs_shortcuts.conan_install_updates = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_source(self, text: str) -> None:
        self._prefs_shortcuts.conan_source = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_build(self, text: str) -> None:
        self._prefs_shortcuts.conan_build = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_package(self, text: str) -> None:
        self._prefs_shortcuts.conan_package = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_exportpkg(self, text: str) -> None:
        self._prefs_shortcuts.conan_export_package = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_test(self, text: str) -> None:
        self._prefs_shortcuts.conan_test_package = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_remove(self, text: str) -> None:
        self._prefs_shortcuts.conan_remove_package = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_cancel(self, text: str) -> None:
        self._prefs_shortcuts.cancel = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_cmakebuildtool(self, text: str) -> None:
        self._prefs_shortcuts.cmake_build_tool = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_cmakebuildtoolverbose(self, text: str) -> None:
        self._prefs_shortcuts.cmake_build_tool_verbose = text or None  # type: ignore
        self.modified.emit()

    def _shortcuts_change_deletecmakecache(self, text: str) -> None:
        self._prefs_shortcuts.delete_cmake_cache = text or None  # type: ignore
        self.modified.emit()

    # -- Recipes --
    def _recipes_load_defaults(self) -> None:
        with RecentRecipeSettingsReader() as settings:
            self._prefs_recipes_model.set_uuids(settings.uuids())

    def _recipes_context_menu(self, position: QtCore.QPoint) -> None:
        selected_rows = self._ui.prefs_recipes_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        selected_index = selected_rows[0]
        uuid = self._prefs_recipes_model.uuid(selected_index.row())
        menu = QtWidgets.QMenu(self)
        menu.addActions(self._ui.prefs_recipes_table.actions())
        forget_recipe_action = menu.actions()[0]
        forget_recipe_action.setData(uuid)
        forget_recipe_action.triggered.connect(self._recipes_forget_recipe)
        menu.addSeparator()
        menu.addMenu(self._recipes_build_change_cache_menu(uuid, menu)).setText(
            "Change local cache to"
        )
        menu.exec_(self._ui.prefs_recipes_table.viewport().mapToGlobal(position))

    def _recipes_build_change_cache_menu(
        self, uuid: QtCore.QUuid, parent_menu: QtWidgets.QMenu
    ) -> QtWidgets.QMenu:
        menu = QtWidgets.QMenu(parent_menu)
        with RecipeSettingsReader.from_uuid(uuid) as settings:
            uuid_local_cache = settings.local_cache_name.resolve()
        with AllNamedLocalCacheSettingsReader() as cache_names:
            for name in cache_names:
                if name == uuid_local_cache:
                    continue
                action = QtGui.QAction(name, self)
                action.setData(uuid)
                action.triggered.connect(self._recipes_change_cache)
                menu.addAction(action)
        return menu

    def _recipes_change_cache(self) -> None:
        selected_rows = self._ui.prefs_recipes_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        selected_index = selected_rows[0]
        path_itemdata = self._prefs_recipes_model.itemData(selected_index)
        if not path_itemdata:
            return
        cache_menu_action = self.sender()
        result = QtWidgets.QMessageBox.question(
            self,
            "Change local cache for recipe",
            "Are you sure you want to change the local cache for recipe "
            f"'{path_itemdata[0]}' to '{cache_menu_action.text()}'",
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return
        settings = RecipeSettings()
        settings.local_cache_name = cache_menu_action.text()
        RecipeSettingsWriter.from_uuid(cache_menu_action.data()).sync(settings)
        self._recipes_load_defaults()

    def _recipes_forget_recipe(self) -> None:
        action = self.sender()
        uuid = action.data()
        with RecipeSettingsReader.from_uuid(uuid) as settings:
            has_editables = settings.editables_count.resolve()
            recipe_path = settings.path.resolve()
        if has_editables:
            QtWidgets.QMessageBox.critical(
                self,
                "Recipe still has editables",
                f"Recipe {recipe_path} still has editable dependencies. "
                "Cannot forget until they are removed.",
            )
            return
        # TODO: this is not ideal, as it's not atomic
        # there are two QSettings created and destroyed
        # so there is a possibility that one part can fail,
        # so the settings can be left in a inconsistent state
        RecentRecipeSettingsDeleter().delete(uuid)
        RecipeSettingsDeleter().delete(uuid)
        self._recipes_load_defaults()

    # -- Recent configs --
    def _recentconfigs_load_defaults(self) -> None:
        with RecentConanConfigSettingsReader() as settings:
            self._prefs_recentconfigs_model.set_paths(settings.paths.resolve())

    def _recentconfigs_context_menu(self, position: QtCore.QPoint) -> None:
        selected_rows = (
            self._ui.prefs_recentconfigs_list.selectionModel().selectedRows()
        )
        if not selected_rows:
            return
        selected_index = selected_rows[0]
        path = self._prefs_recentconfigs_model.path(selected_index.row())
        menu = QtWidgets.QMenu(self)
        menu.addActions(self._ui.prefs_recentconfigs_list.actions())
        forget_config_action = menu.actions()[0]
        forget_config_action.setData(path)
        forget_config_action.triggered.connect(self._recentconfigs_forget_config)
        menu.exec_(self._ui.prefs_recentconfigs_list.viewport().mapToGlobal(position))

    def _recentconfigs_forget_config(self) -> None:
        action = self.sender()
        path = action.data()
        RecentConanConfigSettingsDeleter().delete(path)
        self._recentconfigs_load_defaults()

    # -- Recent remotes --
    def _recentremotes_load_defaults(self) -> None:
        with RecentConanRemotesSettingsReader() as settings:
            self._prefs_recentremotes_model.set_urls(settings.urls.resolve())

    def _recentremotes_context_menu(self, position: QtCore.QPoint) -> None:
        selected_rows = (
            self._ui.prefs_recentremotes_list.selectionModel().selectedRows()
        )
        if not selected_rows:
            return
        selected_index = selected_rows[0]
        url = self._prefs_recentremotes_model.url(selected_index.row())
        menu = QtWidgets.QMenu(self)
        menu.addActions(self._ui.prefs_recentremotes_list.actions())
        forget_config_action = menu.actions()[0]
        forget_config_action.setData(url)
        forget_config_action.triggered.connect(self._recentremotes_forget_config)
        menu.exec_(self._ui.prefs_recentremotes_list.viewport().mapToGlobal(position))

    def _recentremotes_forget_config(self) -> None:
        action = self.sender()
        url = action.data()
        RecentConanRemotesSettingsDeleter().delete(url)
        self._recentremotes_load_defaults()

    def _requires_restart(self) -> None:
        QtWidgets.QMessageBox.information(
            self,
            "Restart required",
            "Changing this preference requires restarting the application to take "
            "effect.",
        )

    def _import_presets(self) -> None:
        prefix_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            caption="Import preferences presets",
            filter="JSON (*.json)",
        )
        if not prefix_path:
            return
        prefix_path_path = pathlib.Path(prefix_path)
        with prefix_path_path.open("rt", encoding="utf-8") as preset_json_file:
            presets = json.load(preset_json_file)
        if "cruiz_presets" not in presets:
            QtWidgets.QMessageBox.critical(
                self,
                "Preference presets",
                f"{prefix_path} is an invalid preference presets file. "
                "Aborting import.",
            )
            return
        LocalCacheSettingsWriter().presets(presets["cruiz_presets"])
        self._current_load_defaults(self._ui.prefs_toolbox.currentIndex())

    def _export_presets(self) -> None:
        prefix_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export preferences presets", "", "JSON files (*.json)"
        )
        if not prefix_path:
            return
        presets: typing.Dict[str, str] = {}
        with LocalCacheSettingsReader() as settings:
            presets.update(settings.presets())  # type: ignore
        if presets:
            prefix_path_path = pathlib.Path(prefix_path)
            with prefix_path_path.open("wt", encoding="utf-8") as preset_json_file:
                json.dump({"cruiz_presets": presets}, preset_json_file, indent=4)

    def _clean_preferences(self) -> None:
        sanitise_settings(self)

    def _restore_defaults(self) -> None:
        result = QtWidgets.QMessageBox.question(
            self,
            "Factory reset",
            (
                "Performing a factory reset will clear all settings and restart cruiz. "
                "Do you want to continue?"
            ),
        )
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            factory_reset()

    def _refresh_shortcut_icons(self) -> None:
        def _set_pixmap(label: QtWidgets.QLabel, name: str) -> None:
            size = 32
            if name.startswith(":/"):
                icon = QtGui.QIcon(name)
            else:
                icon = QtGui.QIcon(f":/icons/{cruiz.globals.get_theme()}/{name}")
            label.setPixmap(icon.pixmap(size, size))

        _set_pixmap(self._ui.shortcut_conan_create, "create.svg")
        _set_pixmap(self._ui.shortcut_conan_create_update, "create.svg")
        _set_pixmap(self._ui.shortcut_conan_install, "install.svg")
        _set_pixmap(self._ui.shortcut_conan_install_update, "install.svg")
        _set_pixmap(self._ui.shortcut_conan_source, "source.svg")
        _set_pixmap(self._ui.shortcut_conan_build, "build.svg")
        _set_pixmap(self._ui.shortcut_conan_export_package, "exportpackage.svg")
        _set_pixmap(self._ui.shortcut_conan_test, "testpackage.svg")
        _set_pixmap(self._ui.shortcut_conan_remove, "removepackage.svg")
        _set_pixmap(self._ui.shortcut_cancel_command, ":/cancel.svg")
        if cruiz.globals.CONAN_MAJOR_VERSION == 1:
            _set_pixmap(self._ui.shortcut_conan_imports, "imports.svg")
            _set_pixmap(self._ui.shortcut_conan_package, "package.svg")
            _set_pixmap(self._ui.shortcut_cmake_build_tool, ":/cmakebuildtool.svg")
            _set_pixmap(
                self._ui.shortcut_cmake_verbose_build_tool,
                ":/cmakebuildtoolverbose.svg",
            )
            _set_pixmap(self._ui.shortcut_delete_cmake_cache, ":/removecmakecache.svg")
        else:
            self._ui.shortcut_conan_imports.hide()
            self._ui.shortcut_conan_package.hide()
            self._ui.shortcut_cmake_build_tool.hide()
            self._ui.shortcut_cmake_verbose_build_tool.hide()
            self._ui.shortcut_delete_cmake_cache.hide()
