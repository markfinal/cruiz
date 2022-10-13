#!/usr/bin/env python3

"""
Dialog for managing local caches
"""

from enum import IntEnum
import os
import platform
import shutil
import stat
import typing

from qtpy import QtCore, QtGui, QtWidgets, PYSIDE2
from cruiz.commands.logdetails import LogDetails

from cruiz.interop.pod import ConanHook
from cruiz.settings.managers.namedlocalcache import (
    NamedLocalCacheSettings,
    NamedLocalCacheSettingsReader,
    NamedLocalCacheSettingsWriter,
    AllNamedLocalCacheSettingsReader,
    NamedLocalCacheDeleter,
    _EnvChangeManagement,
)
from cruiz.settings.managers.recentconanremotes import (
    RecentConanRemotesSettingsReader,
    RecentConanRemotesSettingsWriter,
)
from cruiz.widgets.util import BlockSignals
from cruiz.commands.context import ConanContext, ConanConfigBoolean

from cruiz.revealonfilesystem import reveal_on_filesystem
from cruiz.constants import DEFAULT_CACHE_NAME

if PYSIDE2:
    from cruiz.pyside2.local_cache_manage import Ui_ManageLocalCaches

    QAction = QtWidgets.QAction
else:
    from cruiz.pyside6.local_cache_manage import Ui_ManageLocalCaches

    QAction = QtGui.QAction

from .widgets import (
    NewLocalCacheWizard,
    InstallConfigDialog,
    MoveLocalCacheDialog,
    AddRemoteDialog,
    RemoveLocksDialog,
    RemoveAllPackagesDialog,
    AddExtraProfileDirectoryDialog,
    AddEnvironmentDialog,
    RemoveEnvironmentDialog,
    RunConanCommandDialog,
)


class ManageLocalCachesDialog(QtWidgets.QDialog):
    """
    New Manage Local Caches dialog.
    """

    _modified = QtCore.Signal()
    cache_changed = QtCore.Signal(str)

    class _HooksTableColumnIndex(IntEnum):
        """
        Column indices of the hooks table
        """

        ENABLED = 0
        PATH = 1

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        cache_name_to_open: typing.Optional[str],
    ) -> None:
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        self._ui = Ui_ManageLocalCaches()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        self._ui.new_local_cache_button.clicked.connect(self._new_cache)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(False)
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).clicked.connect(
            self._save_modifications
        )
        # locations
        dir_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        self._ui.conan_user_home.setReadOnly(True)
        open_user_home_action = QAction(dir_icon, "", self)
        open_user_home_action.triggered.connect(self._open_conan_user_home)
        self._ui.conan_user_home.addAction(
            open_user_home_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        self._ui.conan_user_home_short.setReadOnly(True)
        open_short_user_home_action = QAction(dir_icon, "", self)
        open_short_user_home_action.triggered.connect(self._open_conan_user_home_short)
        self._ui.conan_user_home_short.addAction(
            open_short_user_home_action,
            QtWidgets.QLineEdit.TrailingPosition,
        )
        # extra profiles
        self._ui.profilesTableButtons.button(QtWidgets.QDialogButtonBox.Open).setText(
            "+"
        )
        self._ui.profilesTableButtons.button(
            QtWidgets.QDialogButtonBox.Open
        ).clicked.connect(self._profiles_add)
        self._ui.profilesTableButtons.button(QtWidgets.QDialogButtonBox.Close).setText(
            "-"
        )
        self._ui.profilesTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).clicked.connect(self._profiles_remove)
        self._ui.profilesTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).setEnabled(False)
        self._ui.profilesTable.itemSelectionChanged.connect(self._profiles_selection)
        # config
        self._ui.configPrintRunCommands.toggled.connect(
            self._config_toggle_printruncommands
        )
        self._ui.configRevisions.toggled.connect(self._config_toggle_revisions)
        # environments
        # - adding
        self._ui.envTableButtons.button(QtWidgets.QDialogButtonBox.Open).setText("+")
        self._ui.envTableButtons.button(
            QtWidgets.QDialogButtonBox.Open
        ).clicked.connect(self._env_add_plus)
        self._ui.envTableButtons.button(QtWidgets.QDialogButtonBox.Close).setText("-")
        self._ui.envTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).clicked.connect(self._env_add_minus)
        self._ui.envTableButtons.button(QtWidgets.QDialogButtonBox.Close).setEnabled(
            False
        )
        self._ui.envTable.itemSelectionChanged.connect(self._env_add_selection)
        self._ui.envTable.model().dataChanged.connect(self._env_add_changed)
        # - removing
        self._ui.envRemoveButtons.button(QtWidgets.QDialogButtonBox.Open).setText("+")
        self._ui.envRemoveButtons.button(
            QtWidgets.QDialogButtonBox.Open
        ).clicked.connect(self._env_remove_plus)
        self._ui.envRemoveButtons.button(QtWidgets.QDialogButtonBox.Close).setText("-")
        self._ui.envRemoveButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).clicked.connect(self._env_remove_minus)
        self._ui.envRemoveButtons.button(QtWidgets.QDialogButtonBox.Close).setEnabled(
            False
        )
        self._ui.envRemoveList.itemSelectionChanged.connect(self._env_remove_selection)
        self._ui.envRemoveList.model().dataChanged.connect(self._env_remove_changed)
        # remotes
        self._ui.remotesTableButtons.button(QtWidgets.QDialogButtonBox.Open).setText(
            "+"
        )
        self._ui.remotesTableButtons.button(
            QtWidgets.QDialogButtonBox.Open
        ).clicked.connect(self._remotes_add)
        self._ui.remotesTableButtons.button(QtWidgets.QDialogButtonBox.Close).setText(
            "-"
        )
        self._ui.remotesTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).clicked.connect(self._remotes_remove)
        self._ui.remotesTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).setEnabled(False)
        self._ui.remotesTable.itemSelectionChanged.connect(self._remotes_selection)
        self._ui.remotesTable.remotes_reordered.connect(self._remotes_reordered)
        self._ui.remotesTable.remote_enabled.connect(self._remote_enabled)
        # hooks
        self._ui.hooksTable.itemChanged.connect(self._hooks_item_changed)
        # operations
        self._ui.operations_installConfigButton.clicked.connect(
            self._operations_install_config
        )
        self._ui.operations_removeLocksButton.clicked.connect(
            self._operations_remove_locks
        )
        self._ui.operations_removeAllPackagesButton.clicked.connect(
            self._operations_remove_all_packages
        )
        self._ui.moveCacheButton.clicked.connect(self._operations_move_cache)
        self._ui.deleteCacheButton.clicked.connect(self._operations_delete_cache)
        self._ui.runConanCommandButton.clicked.connect(self._operations_run_command)
        # log
        self._ui.localCacheLog.hide()
        self._ui.localCacheLog.customContextMenuRequested.connect(
            self._log_context_menu
        )
        self._log_details = LogDetails(
            self._ui.localCacheLog, self._ui.localCacheLog, True, False, None
        )
        self._log_details.logging.connect(self._ui.localCacheLog.show)
        self._context = ConanContext(DEFAULT_CACHE_NAME, self._log_details)
        self._populate_cache_names(cache_name_to_open)
        self._modifications: typing.Dict[str, typing.Any] = {}
        self._modified.connect(self._on_modification)

    def _open_conan_user_home(self) -> None:
        reveal_on_filesystem(self._ui.conan_user_home.text())

    def _open_conan_user_home_short(self) -> None:
        reveal_on_filesystem(self._ui.conan_user_home_short.text())

    def _on_modification(self) -> None:
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Apply).setEnabled(
            bool(self._modifications)
        )

    def accept(self) -> None:
        if self._modifications:
            self._save_modifications()
        self._context.close()
        super().accept()

    def reject(self) -> None:
        if self._modifications:
            if (
                QtWidgets.QMessageBox.question(
                    self,
                    "Local cache modifications",
                    "Do you want to lose unsaved changes to the local cache?",
                )
                == QtWidgets.QMessageBox.StandardButton.No
            ):
                return
        self._context.close()
        super().reject()

    def _populate_cache_names(
        self, cache_name_to_select: typing.Optional[str] = None
    ) -> None:
        combo = self._ui.local_cache_names
        current_cache_name = combo.currentText()
        combo.currentTextChanged.connect(
            self._update_cache_details
        )  # TODO: should this be moved, as this fn is called multiple times
        with BlockSignals(combo):
            combo.clear()
            with AllNamedLocalCacheSettingsReader() as names:
                combo.addItems(names)
            combo.setCurrentIndex(-1)
        if cache_name_to_select:
            combo.setCurrentText(cache_name_to_select)
        else:
            # no preference, default or the previous selection
            combo.setCurrentText(current_cache_name or DEFAULT_CACHE_NAME)

    def _new_cache(self) -> None:
        dialog = NewLocalCacheWizard(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if dialog.switch_to_new_cache:
                self._populate_cache_names(dialog.cache_name)
            else:
                # slightly faster, as all cache details don't need to be refetched
                with BlockSignals(self._ui.local_cache_names):
                    self._populate_cache_names()
            self.cache_changed.emit(dialog.cache_name)

    def _update_cache_locations(
        self,
        cache_home_dir: typing.Optional[str],
        cache_short_home_dir: typing.Optional[str],
    ) -> None:
        is_windows = platform.system() == "Windows"
        if not is_windows:
            self._ui.loc_conan_user_home_short_label.hide()
            self._ui.conan_user_home_short.hide()
        if self._context.is_default:
            home_dir = QtCore.QStandardPaths.writableLocation(
                QtCore.QStandardPaths.HomeLocation
            )
            self._ui.conan_user_home.setText(home_dir)
            if is_windows:
                drive = QtCore.QStorageInfo(home_dir).name()
                self._ui.conan_user_home_short.setText(drive)
        else:
            assert cache_home_dir
            self._ui.conan_user_home.setText(cache_home_dir)
            if is_windows and cache_short_home_dir is not None:
                self._ui.conan_user_home_short.setText(cache_short_home_dir)
        with NamedLocalCacheSettingsReader(self._context.cache_name) as settings:
            recipe_uuids = settings.recipe_uuids
        self._ui.localCacheRecipeCount.setText(
            f"{len(recipe_uuids)} recipes associated with this cache"
        )

    def _update_cache_profiles(self, extra_profile_dirs: typing.Dict[str, str]) -> None:
        self._ui.profilesTable.setRowCount(0)
        for name, profile_dir in extra_profile_dirs.items():
            self._ui.profilesTable.add_key_value_pair(name, profile_dir)
        self._ui.profilesList.clear()
        for i, (profile_path, profile_text) in enumerate(
            self._context.get_list_of_profiles()
        ):
            self._ui.profilesList.addItem(str(profile_path))
            item = self._ui.profilesList.item(i)
            item.setData(QtCore.Qt.ToolTipRole, profile_text)  # type: ignore[arg-type]

    def _update_cache_config(self) -> None:
        with BlockSignals(self._ui.configPrintRunCommands) as blocked_widget:
            blocked_widget.setCheckState(
                QtCore.Qt.Checked
                if self._context.get_boolean_config(
                    ConanConfigBoolean.PRINT_RUN_COMMANDS, False
                )
                else QtCore.Qt.Unchecked
            )
        with BlockSignals(self._ui.configRevisions) as blocked_widget:
            blocked_widget.setCheckState(
                QtCore.Qt.Checked
                if self._context.get_boolean_config(ConanConfigBoolean.REVISIONS, False)
                else QtCore.Qt.Unchecked
            )

    def _update_cache_environment(
        self, env_added: typing.Dict[str, str], env_removed: typing.List[str]
    ) -> None:
        self._ui.envTable.setRowCount(0)
        for key, value in env_added.items():
            self._ui.envTable.add_key_value_pair(key, value)
        self._ui.envRemoveList.clear()
        for key in env_removed:
            item = QtWidgets.QListWidgetItem(key)
            self._ui.envRemoveList.addItem(item)

    def _update_cache_remotes(self) -> None:
        self._ui.remotesTable.setRowCount(0)
        for remote in self._context.get_remotes_list():
            self._ui.remotesTable.add_remote(remote)

    def _update_cache_hooks(self) -> None:
        self._ui.hooksTable.setRowCount(0)
        hooks = self._context.get_hooks_list()
        self._ui.hooksTable.setRowCount(len(hooks))
        for i, hook in enumerate(hooks):
            enabled_item = QtWidgets.QTableWidgetItem()
            enabled_item.setFlags(
                QtCore.Qt.ItemIsEnabled  # type: ignore
                | QtCore.Qt.ItemIsSelectable
                | QtCore.Qt.ItemIsUserCheckable
            )
            enabled_item.setCheckState(
                QtCore.Qt.Checked if hook.enabled else QtCore.Qt.Unchecked
            )
            name_item = QtWidgets.QTableWidgetItem(hook.path)
            name_item.setFlags(
                QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable  # type: ignore
            )
            with BlockSignals(self._ui.hooksTable) as blocked_widget:
                blocked_widget.setItem(
                    i,
                    ManageLocalCachesDialog._HooksTableColumnIndex.ENABLED,
                    enabled_item,
                )
                blocked_widget.setItem(
                    i, ManageLocalCachesDialog._HooksTableColumnIndex.PATH, name_item
                )

    def _update_cache_details(self, cache_name: str) -> None:
        self._context.change_cache(cache_name)
        with NamedLocalCacheSettingsReader(cache_name) as settings:
            home_dir = settings.home_dir.resolve()
            short_home_dir = settings.short_home_dir.resolve()
            env_added = settings.environment_added.resolve()
            env_removed = settings.environment_removed.resolve()
            extra_profile_dirs = settings.extra_profile_directories.resolve()
            recipe_uuids = settings.recipe_uuids
        self._update_cache_locations(home_dir, short_home_dir)
        self._update_cache_profiles(extra_profile_dirs)
        self._update_cache_config()
        self._update_cache_environment(env_added, env_removed)
        self._update_cache_remotes()
        self._update_cache_hooks()
        can_move = not self._context.is_default
        self._ui.moveCacheButton.setEnabled(can_move)
        can_delete = not self._context.is_default and not recipe_uuids
        self._ui.deleteCacheButton.setEnabled(can_delete)

    def _save_modifications(self) -> None:
        assert self._modifications
        if "Profiles" in self._modifications or "Env" in self._modifications:
            settings_lc = NamedLocalCacheSettings()
            if "Profiles" in self._modifications:
                if "Added" in self._modifications["Profiles"]:
                    for extra_dir in self._modifications["Profiles"]["Added"]:
                        settings_lc.append_extra_profile_directories(extra_dir)
                if "Removed" in self._modifications["Profiles"]:
                    for name in self._modifications["Profiles"]["Removed"]:
                        settings_lc.remove_extra_profile_directories(name)
            if "Env" in self._modifications and self._modifications["Env"].has_change:
                with NamedLocalCacheSettingsReader(
                    self._context.cache_name
                ) as settings:
                    existing_removed = settings.environment_removed.resolve()
                settings_lc.sync_env_changes(
                    existing_removed, self._modifications["Env"]
                )
            NamedLocalCacheSettingsWriter(self._context.cache_name).sync(settings_lc)
            if "Profiles" in self._modifications:
                del self._modifications["Profiles"]
            if "Env" in self._modifications:
                del self._modifications["Env"]
        if "Config" in self._modifications:
            for config, value in self._modifications["Config"].items():
                self._context.set_boolean_config(config, value)
            del self._modifications["Config"]
        if "Remotes" in self._modifications:
            # brute force write everything back to settings
            self._context.remotes_sync(self._ui.remotesTable.remotes_list())
            if "Add" in self._modifications["Remotes"]:
                with RecentConanRemotesSettingsReader() as settings_remotes:
                    urls = settings_remotes.urls.resolve()
                for remote in self._modifications["Remotes"]["Add"]:
                    if remote.url not in urls:
                        urls.append(remote.url)
                settings_remotes.urls = urls  # type: ignore[assignment]
                RecentConanRemotesSettingsWriter().sync(settings_remotes)
            del self._modifications["Remotes"]
        if "Hooks" in self._modifications:
            self._context.hooks_sync(self._modifications["Hooks"])
            del self._modifications["Hooks"]
        assert not self._modifications
        self._modified.emit()
        # need to refresh if it was Apply
        if self.sender() == self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.Apply):
            self._update_cache_details(self._context.cache_name)
        self.cache_changed.emit(self._context.cache_name)

    def _remotes_add(self) -> None:
        dialog = AddRemoteDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self._ui.remotesTable.add_remote(dialog.new_remote)
            if "Remotes" not in self._modifications:
                self._modifications["Remotes"] = {}
            if "Add" not in self._modifications:
                self._modifications["Remotes"]["Add"] = []
            self._modifications["Remotes"]["Add"].append(dialog.new_remote)
            self._modified.emit()

    def _remotes_remove(self) -> None:
        remote_removed = self._ui.remotesTable.remove_selected()
        if "Remotes" not in self._modifications:
            self._modifications["Remotes"] = {}
        if "Add" in self._modifications["Remotes"]:
            index = next(
                (
                    i
                    for i, remote in enumerate(self._modifications["Remotes"]["Add"])
                    if remote.name == remote_removed.name
                ),
                -1,
            )
            if index >= 0:
                del self._modifications["Remotes"]["Add"][index]
                if not self._modifications["Remotes"]["Add"]:
                    del self._modifications["Remotes"]["Add"]
                if not self._modifications["Remotes"]:
                    del self._modifications["Remotes"]
                if (
                    "Remotes" in self._modifications
                    and "Reordered" in self._modifications["Remotes"]
                ):
                    # has the removal of the addition now put the
                    # table back into it's original order?
                    if self._ui.remotesTable.same(self._context.get_remotes_list()):
                        del self._modifications["Remotes"]["Reordered"]
                        if not self._modifications["Remotes"]:
                            del self._modifications["Remotes"]
        else:
            if "Remove" not in self._modifications["Remotes"]:
                self._modifications["Remotes"]["Remove"] = []
            self._modifications["Remotes"]["Remove"].append(remote_removed.name)
        self._modified.emit()

    def _remotes_selection(self) -> None:
        self._ui.remotesTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).setEnabled(bool(self._ui.remotesTable.selectedRanges()))

    def _remotes_reordered(self) -> None:
        if self._ui.remotesTable.same(self._context.get_remotes_list()):
            del self._modifications["Remotes"]["Reordered"]
            if not self._modifications["Remotes"]:
                del self._modifications["Remotes"]
        else:
            if "Remotes" not in self._modifications:
                self._modifications["Remotes"] = {}
            if "Reordered" not in self._modifications["Remotes"]:
                self._modifications["Remotes"]["Reordered"] = True
        self._modified.emit()

    def _remote_enabled(self, name: str, state: QtCore.Qt.CheckState) -> None:
        remotes = self._context.get_remotes_list()
        try:
            remote = next(item for item in remotes if item.name == name)
            if remote.enabled == bool(state):
                self._modifications["Remotes"]["Toggled"].remove(name)
                if not self._modifications["Remotes"]["Toggled"]:
                    del self._modifications["Remotes"]["Toggled"]
                if not self._modifications["Remotes"]:
                    del self._modifications["Remotes"]
            else:
                if "Remotes" not in self._modifications:
                    self._modifications["Remotes"] = {}
                if "Toggled" not in self._modifications["Remotes"]:
                    self._modifications["Remotes"]["Toggled"] = []
                self._modifications["Remotes"]["Toggled"].append(name)
        except StopIteration:
            assert "Remotes" in self._modifications
            assert "Add" in self._modifications["Remotes"]
            remote = next(
                item
                for item in self._modifications["Remotes"]["Add"]
                if item.name == name
            )
            # this was simply to check that the modifications contained the remote
            # toggled since the table holds the truth, not the modifications
        self._modified.emit()

    def _hooks_item_changed(self, item: QtWidgets.QTableWidgetItem) -> None:
        if item.column() == ManageLocalCachesDialog._HooksTableColumnIndex.ENABLED:
            path_item = self._ui.hooksTable.item(
                item.row(), ManageLocalCachesDialog._HooksTableColumnIndex.PATH
            )
            hook_path = path_item.text().strip()
            item_enabled = bool(item.checkState())
            hooks = self._context.get_hooks_list()
            hook = next(item for item in hooks if item.has_path(hook_path))
            assert hook
            if item_enabled == hook.enabled:
                hook_unchanged = next(
                    item
                    for item in self._modifications["Hooks"]
                    if item.has_path(hook_path)
                )
                self._modifications["Hooks"].remove(hook_unchanged)
                if not self._modifications["Hooks"]:
                    del self._modifications["Hooks"]
            else:
                if "Hooks" not in self._modifications:
                    self._modifications["Hooks"] = []
                self._modifications["Hooks"].append(ConanHook(hook_path, item_enabled))
            self._modified.emit()

    def _operations_install_config(self) -> None:
        if (
            InstallConfigDialog(self._context, self).exec_()
            == QtWidgets.QDialog.Accepted
        ):
            cache_name = self._context.cache_name
            self._update_cache_details(cache_name)
            self.cache_changed.emit(cache_name)

    def _operations_remove_locks(self) -> None:
        RemoveLocksDialog(self._context, self).exec_()

    def _operations_remove_all_packages(self) -> None:
        result = QtWidgets.QMessageBox.question(
            self,
            "Package deletion",
            "Are you sure you want to delete all packages from this local cache?",
        )
        if result == QtWidgets.QMessageBox.StandardButton.Yes:
            RemoveAllPackagesDialog(self._context, self).exec_()

    def _operations_move_cache(self) -> None:
        if (
            MoveLocalCacheDialog(self._context, self).exec_()
            == QtWidgets.QDialog.Accepted
        ):
            self._update_cache_details(self._context.cache_name)

    @staticmethod
    def _delete_tree_with_readonly_files(dir_path: str) -> None:
        if not os.path.isdir(dir_path):
            return

        def make_writeable(action: typing.Any, name: str, exc: typing.Any) -> None:
            # pylint: disable=unused-argument
            if exc[0] is PermissionError:
                os.chmod(name, stat.S_IWRITE)
                os.remove(name)
            else:
                raise exc[1]

        shutil.rmtree(dir_path, onerror=make_writeable)

    def _operations_delete_cache(self) -> None:
        cache_name = self._context.cache_name
        result = QtWidgets.QMessageBox.question(
            self,
            "Local cache deletion",
            f"Are you sure you want to delete the local cache {cache_name}?",
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return
        with NamedLocalCacheSettingsReader(cache_name) as settings:
            home_dir = settings.home_dir.resolve()
            short_home_dir = settings.short_home_dir.resolve()

        assert home_dir  # because it's non-default
        conan_home_dir = os.path.join(home_dir, ".conan")
        # since this is destructive, check again
        result = QtWidgets.QMessageBox.question(
            self,
            "Local cache deletion",
            f"Please confirm you want to delete the directories {conan_home_dir} and "
            f"{short_home_dir}?"
            if short_home_dir
            else f"Please confirm you want to delete the directory {conan_home_dir}?",
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return
        ManageLocalCachesDialog._delete_tree_with_readonly_files(conan_home_dir)
        if short_home_dir:
            ManageLocalCachesDialog._delete_tree_with_readonly_files(short_home_dir)
        NamedLocalCacheDeleter().delete(cache_name)
        self._ui.local_cache_names.removeItem(
            self._ui.local_cache_names.findText(cache_name)
        )
        self._ui.local_cache_names.setCurrentIndex(0)  # default
        self.cache_changed.emit(cache_name)

    def _operations_run_command(self) -> None:
        RunConanCommandDialog(self._context.cache_name, self).exec_()

    def _profiles_add(self) -> None:
        dialog = AddExtraProfileDirectoryDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            extra = dialog.extra
            self._ui.profilesTable.add_key_value_pair(extra.name, extra.directory)
            if "Profiles" not in self._modifications:
                self._modifications["Profiles"] = {}
            if "Added" not in self._modifications["Profiles"]:
                self._modifications["Profiles"]["Added"] = []
            self._modifications["Profiles"]["Added"].append(extra)
            self._modified.emit()

    def _profiles_remove(self) -> None:
        name_removed = self._ui.profilesTable.remove_selected()
        if "Profiles" not in self._modifications:
            self._modifications["Profiles"] = {}
        if "Added" in self._modifications["Profiles"]:
            try:
                profile_add_removed = next(
                    item
                    for item in self._modifications["Profiles"]["Added"]
                    if item.name == name_removed
                )
                self._modifications["Profiles"]["Added"].remove(profile_add_removed)
                if not self._modifications["Profiles"]["Added"]:
                    del self._modifications["Profiles"]["Added"]
                if not self._modifications["Profiles"]:
                    del self._modifications["Profiles"]
                self._modified.emit()
                return
            except StopIteration:
                pass
        if "Removed" not in self._modifications["Profiles"]:
            self._modifications["Profiles"]["Removed"] = []
        self._modifications["Profiles"]["Removed"].append(name_removed)
        self._modified.emit()

    def _profiles_selection(self) -> None:
        self._ui.profilesTableButtons.button(
            QtWidgets.QDialogButtonBox.Close
        ).setEnabled(bool(self._ui.profilesTable.selectedRanges()))

    def _config_toggle(self, checked: bool, config: ConanConfigBoolean) -> None:
        if checked == self._context.get_boolean_config(config, False):
            del self._modifications["Config"][config]
            if not self._modifications["Config"]:
                del self._modifications["Config"]
        else:
            if "Config" not in self._modifications:
                self._modifications["Config"] = {}
            self._modifications["Config"][config] = checked
        self._modified.emit()

    def _config_toggle_printruncommands(self, checked: bool) -> None:
        self._config_toggle(checked, ConanConfigBoolean.PRINT_RUN_COMMANDS)

    def _config_toggle_revisions(self, checked: bool) -> None:
        self._config_toggle(checked, ConanConfigBoolean.REVISIONS)

    def _env_add_plus(self) -> None:
        dialog = AddEnvironmentDialog(self._context, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_env = dialog.environment_variable
            self._ui.envTable.add_key_value_pair(new_env.key, new_env.value)
            if "Env" not in self._modifications:
                self._modifications["Env"] = _EnvChangeManagement()
            self._modifications["Env"].key_required(new_env.key, new_env.value)
            self._modified.emit()

    def _env_add_minus(self) -> None:
        key_removed = self._ui.envTable.remove_selected()
        if "Env" not in self._modifications:
            self._modifications["Env"] = _EnvChangeManagement()
        self._modifications["Env"].key_not_required(key_removed)
        if not self._modifications["Env"].has_change:
            del self._modifications["Env"]
        self._modified.emit()

    def _env_add_selection(self) -> None:
        self._ui.envTableButtons.button(QtWidgets.QDialogButtonBox.Close).setEnabled(
            bool(self._ui.envTable.selectedRanges())
        )

    def _env_add_changed(
        self,
        top_left: QtCore.QModelIndex,
        bottom_right: QtCore.QModelIndex,
        roles: typing.List[int],
    ) -> None:
        assert top_left == bottom_right
        row_index = top_left.row()
        new_value = top_left.data(0)
        with NamedLocalCacheSettingsReader(self._context.cache_name) as settings:
            key, prev_value = settings.environment_added_at(row_index)
        if new_value == prev_value:
            return
        if "Env" not in self._modifications:
            self._modifications["Env"] = _EnvChangeManagement()
        self._modifications["Env"].key_required(key, new_value)
        self._modified.emit()

    def _env_remove_plus(self) -> None:
        dialog = RemoveEnvironmentDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_item = QtWidgets.QListWidgetItem(dialog.name)
            self._ui.envRemoveList.addItem(new_item)
            if "Env" not in self._modifications:
                self._modifications["Env"] = _EnvChangeManagement()
            self._modifications["Env"].key_never_required(dialog.name)
            self._modified.emit()

    def _env_remove_minus(self) -> None:
        items_selected = self._ui.envRemoveList.selectedItems()
        assert len(items_selected) == 1
        item_removed = self._ui.envRemoveList.takeItem(
            self._ui.envRemoveList.row(items_selected[0])
        )
        key_removed = item_removed.text()
        if "Env" not in self._modifications:
            self._modifications["Env"] = _EnvChangeManagement()
        self._modifications["Env"].key_not_never_required(key_removed)
        if not self._modifications["Env"].has_change:
            del self._modifications["Env"]
        self._modified.emit()

    def _env_remove_selection(self) -> None:
        self._ui.envRemoveButtons.button(QtWidgets.QDialogButtonBox.Close).setEnabled(
            bool(self._ui.envRemoveList.selectedItems())
        )

    def _env_remove_changed(
        self,
        top_left: QtCore.QModelIndex,
        bottom_right: QtCore.QModelIndex,
        roles: typing.List[int],
    ) -> None:
        assert top_left == bottom_right
        row_index = top_left.row()
        new_value = top_left.data(0)
        # TODO: environment_added_at not correct, as not returning a pair
        with NamedLocalCacheSettingsReader(self._context.cache_name) as settings:
            key, prev_value = settings.environment_added_at(row_index)
        if new_value == prev_value:
            return
        assert "Env" in self._modifications
        assert isinstance(self._modifications["Env"], _EnvChangeManagement)
        self._modifications["Env"].key_never_required(key)
        self._modified.emit()

    def _log_context_menu(self, position: QtCore.QPoint) -> None:
        menu = self.sender().createStandardContextMenu(position)
        menu.addSeparator()
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self._clear_log)
        menu.addAction(clear_action)
        menu.exec_(self.sender().viewport().mapToGlobal(position))

    def _clear_log(self) -> None:
        self._ui.localCacheLog.clear()
        self._ui.localCacheLog.hide()
