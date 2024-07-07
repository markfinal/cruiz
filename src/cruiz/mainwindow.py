#!/usr/bin/env python3

"""
The Qt main window of the application
"""

from __future__ import annotations

from functools import partial
import importlib.util
import logging
import os
import pathlib
import platform
import subprocess
import time
import typing

from qtpy import QtCore, QtGui, QtWidgets
import psutil

from cruiz.exceptions import (
    InconsistentSettingsError,
    RecipeAlreadyOpenError,
    RecipeDoesNotExistError,
    RecipeInspectionError,
)

from cruiz.recipe.recipewidget import RecipeWidget
from cruiz.settings.managers.recipe import (
    RecipeSettings,
    RecipeSettingsReader,
    RecipeSettingsWriter,
)
from cruiz.settings.preferencesdialog import PreferencesDialog
from cruiz.settings.managers.generalpreferences import GeneralSettingsReader
from cruiz.settings.managers.recentrecipes import (
    RecentRecipeSettingsReader,
    RecentRecipeSettingsWriter,
    RecentRecipeSettingsDeleter,
)
from cruiz.settings.managers.cmakepreferences import CMakeSettingsReader
from cruiz.settings.managers.ninjapreferences import NinjaSettingsReader
from cruiz.settings.managers.compilercachepreferences import CompilerCacheSettingsReader
from cruiz.settings.managers.recipe import RecipeSettingsDeleter
from cruiz.widgets import (
    AboutDialog,
    log_created_widget,
)
from cruiz.manage_local_cache import ManageLocalCachesDialog

from cruiz.environ import EnvironSaver
from cruiz.remote_browser.remotebrowser import RemoteBrowserDock

from cruiz.load_recipe.loadrecipewizard import LoadRecipeWizard

import cruiz.config

import cruiz.globals
import cruiz.runcommands

logger = logging.getLogger(__name__)


class MainWindow(QtWidgets.QMainWindow):
    """
    The main window of the application
    """

    # pylint: disable=too-many-instance-attributes, too-many-locals

    profile_dirs_changed = QtCore.Signal()
    remote_added_to_cache = QtCore.Signal(str)
    preferences_updated = QtCore.Signal()
    local_cache_changed = QtCore.Signal(str)
    theme_changed = QtCore.Signal(str)

    def __del__(self) -> None:
        logger.debug("-=%d", id(self))

    def __init__(self) -> None:
        # pylint: disable=too-many-statements, global-statement
        super().__init__()
        log_created_widget(self, logger)

        assert not cruiz.globals.CRUIZ_MAINWINDOW

        qApp.styleHints().colorSchemeChanged.connect(  # type: ignore # noqa: F821
            self._on_platform_theme_changed
        )
        self._on_platform_theme_changed(
            qApp.styleHints().colorScheme()  # type: ignore # noqa: F821
        )

        self._systray = None
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self._app_icon = QtGui.QIcon(":/cruiz.png")
            self._app_menu = QtWidgets.QMenu()
            self._systray = QtWidgets.QSystemTrayIcon(self._app_icon, self)
            self._systray.setContextMenu(self._app_menu)
            self._systray.show()

        mdi_area = QtWidgets.QMdiArea()
        mdi_area.setViewMode(QtWidgets.QMdiArea.TabbedView)
        mdi_area.setDocumentMode(True)
        mdi_area.setTabsClosable(True)
        mdi_area.setTabsMovable(True)
        self.setCentralWidget(mdi_area)

        self._remote_browser_dock = RemoteBrowserDock(self)
        self.local_cache_changed.connect(
            self._remote_browser_dock.on_local_cache_modified
        )
        self.addDockWidget(
            QtCore.Qt.RightDockWidgetArea,
            self._remote_browser_dock,
        )

        open_recipe_action = QtGui.QAction("Open recipe...", self)
        open_recipe_action.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        open_recipe_action.triggered.connect(self._open_recipe)

        exit_action = QtGui.QAction("&Quit", self)
        exit_action.setMenuRole(QtGui.QAction.QuitRole)
        exit_action.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        exit_action.setStatusTip("Quit application")
        exit_action.triggered.connect(
            qApp.closeAllWindows,  # type: ignore # noqa: F821
            QtCore.Qt.QueuedConnection,
        )

        # need a clone of the exit action without the menu role to
        # appear on the systrayicon
        systray_exit_icon = QtGui.QAction("&Quit", self)
        systray_exit_icon.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        systray_exit_icon.setStatusTip("Quit application")
        systray_exit_icon.triggered.connect(
            qApp.closeAllWindows,  # type: ignore # noqa: F821
            QtCore.Qt.QueuedConnection,
        )
        if QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            self._app_menu.addAction(systray_exit_icon)

        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        self._recent_recipe_menu = QtWidgets.QMenu("Recent recipes", file_menu)
        file_menu.aboutToShow.connect(self._rebuild_recent_recipe_menu)
        file_menu.addAction(open_recipe_action)
        file_menu.addMenu(self._recent_recipe_menu)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")
        edit_preferences_action = QtGui.QAction("Preferences...", self)
        edit_preferences_action.setMenuRole(QtGui.QAction.PreferencesRole)
        edit_preferences_action.triggered.connect(self._edit_preferences_new)
        edit_menu.addAction(edit_preferences_action)
        manage_local_caches_action = QtGui.QAction("Manage local caches...", self)
        manage_local_caches_action.triggered.connect(self._manage_local_caches)
        edit_menu.addAction(manage_local_caches_action)

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(self._remote_browser_dock.toggleViewAction())

        help_menu = menubar.addMenu("&Help")
        about_cruiz_action = QtGui.QAction("About cruiz...", self)
        about_cruiz_action.setMenuRole(QtGui.QAction.AboutRole)
        about_cruiz_action.triggered.connect(self._about_cruiz)
        help_menu.addAction(about_cruiz_action)
        about_qt_action = QtGui.QAction("About Qt...", self)
        about_qt_action.setMenuRole(QtGui.QAction.AboutQtRole)
        about_qt_action.triggered.connect(QtWidgets.QApplication.aboutQt)
        help_menu.addAction(about_qt_action)
        icon_license_action = QtGui.QAction("Icon licenses...", self)
        icon_license_action.triggered.connect(self._icon_license)
        help_menu.addAction(icon_license_action)

        self._ccache_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._ccache_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._ccache_label)

        self._sccache_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._sccache_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._sccache_label)

        self._buildcache_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._buildcache_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._buildcache_label)

        self._ssh_agent_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._ssh_agent_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._ssh_agent_label)
        self._configure_ssh_agent_statusbar()

        self._compiler_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._compiler_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._compiler_label)

        self._cmake_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._cmake_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._cmake_label)

        self._ninja_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._ninja_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._ninja_label)

        self._conan_label: QtWidgets.QLabel = QtWidgets.QLabel()
        self._conan_label.setFrameStyle(
            QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken
        )
        self.statusBar().addPermanentWidget(self._conan_label)

        self._warning_label = QtWidgets.QLabel()
        self._warning_label.setPixmap(
            self.style()
            .standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning)
            .pixmap(32, 32)
        )
        self.statusBar().addPermanentWidget(self._warning_label)
        self._warning_label.hide()
        self._warning_label.setContextMenuPolicy(QtGui.Qt.CustomContextMenu)
        self._warning_label.customContextMenuRequested.connect(
            self._on_warning_label_menu
        )

        self._status_file_watcher: QtCore.QFileSystemWatcher = (
            QtCore.QFileSystemWatcher()
        )

        self._refresh_status_bar()

        # deferred until the next event loop, to take into account files being
        # removed and readded by package managers like pip
        self._status_file_watcher.fileChanged.connect(
            self._refresh_status_bar,
            QtCore.Qt.QueuedConnection,
        )

        self.setWindowTitle(qApp.applicationName())  # type: ignore # noqa: F821

        cruiz.globals.CRUIZ_MAINWINDOW = self

    def _on_warning_label_menu(self, position: QtCore.QPoint) -> None:
        action = QtGui.QAction("Dismiss", self)
        action.triggered.connect(self._on_warning_label_dismiss)
        menu = QtWidgets.QMenu(self)
        menu.addAction(action)
        menu.exec_(self.sender().mapToGlobal(position))

    def _on_warning_label_dismiss(self) -> None:
        self._warning_label.setToolTip("")
        self._warning_label.hide()

    def _configure_ssh_agent_statusbar(self) -> None:
        ssh_agent_pid = None
        ssh_agent_text = "SSH agent"
        ssh_agent_color = "red"
        ssh_agent_tooltip = "Not found"
        # find the ssh-agent if it is running
        for process in psutil.process_iter():
            try:
                if "ssh-agent" in process.name():
                    ssh_agent_pid = process.pid
                    ssh_agent_color = "darkorange"
                    ssh_agent_tooltip = "Agent detected"
                    break
            except psutil.NoSuchProcess:
                continue
        if ssh_agent_pid:
            try:
                ssh_add_list_capture = cruiz.runcommands.run_get_combined_output(
                    ["ssh-add", "-l"],
                    check=True,
                    timeout=3,
                )
                identities = ssh_add_list_capture.splitlines()
                ssh_agent_tooltip = f"SSH agent PID {ssh_agent_pid}\n" + " ".join(
                    identities
                )
                ssh_agent_color = "green"
            except subprocess.CalledProcessError as exc:
                error_text = exc.output.strip()
                ssh_agent_tooltip = (
                    f"SSH agent PID {ssh_agent_pid}\n"
                    f"Cannot determine identities: {error_text}"
                )
            except subprocess.TimeoutExpired as exc:
                error_text = exc.output.strip() if exc.output else ""
                ssh_agent_tooltip = (
                    f"SSH agent PID {ssh_agent_pid}\n"
                    f"Timed out communicating with ssh-agent: {error_text}"
                )
                ssh_agent_color = "red"
        self._ssh_agent_label.setText(ssh_agent_text)
        self._ssh_agent_label.setStyleSheet(f"QLabel {{color:{ssh_agent_color};}}")
        self._ssh_agent_label.setToolTip(ssh_agent_tooltip)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        self.centralWidget().closeAllSubWindows()
        if self.centralWidget().subWindowList():
            # if any recipe widget has blocked close, do not continue
            event.ignore()
            return
        self.removeDockWidget(self._remote_browser_dock)
        self._remote_browser_dock.cleanup()
        cruiz.globals.CRUIZ_MAINWINDOW = None
        super().closeEvent(event)

    def _indicate_recipe_settings_issue(self) -> None:
        self._warning_label.show()
        self._warning_label.setToolTip(
            "Issue found with recipe settings. Please clean via the preferences"
        )

    def _rebuild_recent_recipe_menu(self) -> None:
        self._recent_recipe_menu.clear()
        with RecentRecipeSettingsReader() as recent_reader:
            uuids = recent_reader.uuids()
        has_recipe_settings_issue = False
        all_uuids_with_settings = RecipeSettings().all_uuids
        for uuid in uuids:
            with RecipeSettingsReader.from_uuid(uuid) as settings:
                path = settings.path.resolve()
                if not path:
                    has_recipe_settings_issue = True
                    continue
                recipe_path = pathlib.Path(path)
                if not recipe_path.exists():
                    has_recipe_settings_issue = True
                    # can drop through even though the path doesn't exist
                attributes = settings.attribute_overrides.resolve()
            label = (
                f"{recipe_path} [v{attributes['version']}]"
                if "version" in attributes
                else str(recipe_path)
            )
            recent_recipe_action = QtGui.QAction(label, self)
            recent_recipe_action.triggered.connect(
                partial(self.load_recipe, recipe_path, uuid)
            )
            self._recent_recipe_menu.addAction(recent_recipe_action)
            recent_recipe_action.setEnabled(not self.is_recipe_active(uuid))
            all_uuids_with_settings.remove(uuid)
        self._recent_recipe_menu.setEnabled(len(uuids) > 0)
        if all_uuids_with_settings:
            has_recipe_settings_issue = True
        if has_recipe_settings_issue:
            self._indicate_recipe_settings_issue()

    def load_recipe(
        self,
        recipe_path: pathlib.Path,
        recipe_uuid: typing.Optional[QtCore.QUuid] = None,
        original_recipe: typing.Optional[RecipeWidget] = None,
    ) -> None:
        # pylint: disable=too-many-branches, too-many-statements
        """
        Load the Conan recipe into a usable environment
        """

        try:
            wizard = LoadRecipeWizard(
                self,
                recipe_path,
                recipe_uuid,
                original_recipe.recipe if original_recipe else None,
            )
            if wizard.disambiguation_required:
                if wizard.exec_() == QtWidgets.QDialog.Accepted:
                    if wizard.has_load_errors:
                        return
                    recipe_uuid = wizard.uuid
                    if recipe_uuid:
                        wizard.validate()
                else:
                    return
        except RecipeDoesNotExistError:
            result = QtWidgets.QMessageBox.question(
                self,
                "Recipe does not exist",
                f"The recipe at {str(recipe_path)} no longer exists. \
Remove from the recent list?",
            )
            if result == QtWidgets.QMessageBox.StandardButton.Yes:
                # TODO: this is not ideal, as it's not atomic
                # there are two QSettings created and destroyed
                # so there is a possibility that one part can fail,
                # so the settings can be left in a inconsistent state
                assert recipe_uuid
                RecentRecipeSettingsDeleter().delete(recipe_uuid)
                RecipeSettingsDeleter().delete(recipe_uuid)
            return
        except RecipeAlreadyOpenError:
            QtWidgets.QMessageBox.information(
                self,
                "Recipe already open",
                f"The recipe at {str(recipe_path)} is already open",
            )
            return
        except InconsistentSettingsError:
            self._indicate_recipe_settings_issue()
            return

        recipe_uuid = recipe_uuid or QtCore.QUuid.createUuid()

        # TODO: would be better to write both UUID and recipe details in one scope
        exists = RecentRecipeSettingsWriter().make_current(recipe_uuid)
        if not exists:
            settings = RecipeSettings()
            settings.path = str(recipe_path)  # type: ignore
            settings.local_cache_name = wizard.local_cache  # type: ignore
            settings.profile = wizard.initial_profile  # type: ignore
            if wizard.recipe_version:
                settings.append_attribute(
                    {"version": wizard.recipe_version}  # type: ignore
                )
            RecipeSettingsWriter.from_uuid(recipe_uuid).sync(settings)

        recipe_widget = RecipeWidget(recipe_path, recipe_uuid, wizard.local_cache)
        self.local_cache_changed.connect(recipe_widget.on_local_cache_changed)
        self.preferences_updated.connect(recipe_widget.on_preferences_update)
        self.centralWidget().addSubWindow(recipe_widget)
        recipe_widget.show()
        recipe_widget.setFocus(QtCore.Qt.ActiveWindowFocusReason)
        try:
            recipe_widget.post_init()
        except RecipeInspectionError:
            # this error has already been posted to the log window
            recipe_widget.failed_to_load()

    def _open_recipe(self) -> None:
        # TODO: what to do when the directory doesn't exist?
        with GeneralSettingsReader() as settings:
            default_recipe_dir = (
                settings.default_recipe_directory.resolve() or QtCore.QDir.homePath()
            )
        conan_file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            caption="Load Conan package recipe",
            dir=default_recipe_dir,
            filter="Conan Recipe (*.py *.txt)",
        )
        if not conan_file_path:
            return
        self.load_recipe(pathlib.Path(conan_file_path))

    def _edit_preferences_new(self) -> None:
        dialog = PreferencesDialog()
        dialog.preferences_updated.connect(self.preferences_updated)
        dialog.exec_()

    def _manage_local_caches(self, cache_name: typing.Optional[str] = None) -> None:
        dialog = ManageLocalCachesDialog(self, cache_name)
        dialog.cache_changed.connect(self.local_cache_changed)
        dialog.exec_()

    def _refresh(self) -> None:
        self._refresh_status_bar()

    def _refresh_status_bar(self) -> None:
        # pylint: disable=too-many-branches, too-many-statements

        # TODO: this is truly awful, but give a package manager a chance to delete and
        # rewrite upgrades to packages, otherwise this code might be run when at the
        # time when files don't exist temporarily
        time.sleep(1)

        def statusbar_tool(
            tooldesc: str,
            toolpath: str,
            tool_get_version: typing.Callable[[str], str],
            label: QtWidgets.QLabel,
        ) -> None:
            label.setText(tooldesc)
            if toolpath:
                self._status_file_watcher.addPath(toolpath)
                out = tool_get_version(toolpath)
                if out:
                    version = out.splitlines()[0]
                else:
                    version = "No version discovered"

                tooltip = f"Path\t{toolpath}\nVersion\t{version}"
                label.setToolTip(tooltip)
            else:
                label.setStyleSheet("QLabel {color:red;}")
                label.setToolTip("Not found")

        system = platform.system()
        if system == "Windows":
            compiler_desc = "cl.exe"
            compiler_version_query = (
                lambda path: cruiz.runcommands.run_get_combined_output([path])
            )
        elif system == "Linux":
            compiler_desc = "gcc"
            compiler_version_query = (
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                )
            )
        elif system == "Darwin":
            compiler_desc = "clang"
            compiler_version_query = (
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                )
            )
        compiler_path = QtCore.QStandardPaths.findExecutable(compiler_desc)
        statusbar_tool(
            compiler_desc,
            compiler_path,
            compiler_version_query,
            self._compiler_label,
        )

        with EnvironSaver():
            with CMakeSettingsReader() as settings_cmake:
                cmake_dir = settings_cmake.bin_directory.resolve()
            if cmake_dir:
                os.environ["PATH"] = (
                    QtCore.QDir.toNativeSeparators(cmake_dir)
                    + os.pathsep
                    + os.environ.get("PATH", "")
                )
            cmake_exe_path = QtCore.QStandardPaths.findExecutable("cmake")
            statusbar_tool(
                "cmake",
                cmake_exe_path,
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                ),
                self._cmake_label,
            )

            with NinjaSettingsReader() as settings_ninja:
                ninja_dir = settings_ninja.bin_directory.resolve()
            if ninja_dir:
                os.environ["PATH"] = (
                    QtCore.QDir.toNativeSeparators(ninja_dir)
                    + os.pathsep
                    + os.environ.get("PATH", "")
                )
            ninja_exe_path = QtCore.QStandardPaths.findExecutable("ninja")
            statusbar_tool(
                "ninja",
                ninja_exe_path,
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                ),
                self._ninja_label,
            )

            with CompilerCacheSettingsReader() as settings_compilercache:
                ccache_dir = settings_compilercache.ccache_bin_directory.resolve()
                sccache_dir = settings_compilercache.sccache_bin_directory.resolve()
                buildcache_dir = (
                    settings_compilercache.buildcache_bin_directory.resolve()
                )

            if ccache_dir:
                os.environ["PATH"] = (
                    QtCore.QDir.toNativeSeparators(ccache_dir)
                    + os.pathsep
                    + os.environ.get("PATH", "")
                )
            ccache_exe_path = QtCore.QStandardPaths.findExecutable("ccache")
            statusbar_tool(
                "ccache",
                ccache_exe_path,
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                ),
                self._ccache_label,
            )

            if sccache_dir:
                os.environ["PATH"] = (
                    QtCore.QDir.toNativeSeparators(sccache_dir)
                    + os.pathsep
                    + os.environ.get("PATH", "")
                )
            sccache_exe_path = QtCore.QStandardPaths.findExecutable("sccache")
            statusbar_tool(
                "sccache",
                sccache_exe_path,
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                ),
                self._sccache_label,
            )

            if buildcache_dir:
                os.environ["PATH"] = (
                    QtCore.QDir.toNativeSeparators(buildcache_dir)
                    + os.pathsep
                    + os.environ.get("PATH", "")
                )
            buildcache_exe_path = QtCore.QStandardPaths.findExecutable("buildcache")
            statusbar_tool(
                "buildcache",
                buildcache_exe_path,
                lambda path: cruiz.runcommands.run_get_combined_output(
                    [path, "--version"]
                ),
                self._buildcache_label,
            )

        def get_conan_location() -> str:
            spec = importlib.util.find_spec("conan")
            assert spec is not None
            assert spec.origin is not None
            return os.fspath(pathlib.Path(spec.origin).parent)

        def get_conan_version_output(path: str) -> str:
            return cruiz.globals.CONAN_FULL_VERSION

        statusbar_tool(
            "conan",
            get_conan_location(),
            get_conan_version_output,
            self._conan_label,
        )

    def _about_cruiz(self) -> None:
        AboutDialog(self).exec_()

    def _icon_license(self) -> None:
        license_files = [
            "iconlicense.pdf",
            "iconlicense_cruise.pdf",
        ]
        for license in license_files:
            temp_dir = QtCore.QDir(
                QtCore.QStandardPaths.writableLocation(
                    QtCore.QStandardPaths.TempLocation
                )
            )
            temp_path = temp_dir.absoluteFilePath(license)
            if QtCore.QFile.exists(temp_path):
                # file may be read-only when copied from resources,
                # so make writeable and remove it
                perms = QtCore.QFile.permissions(temp_path)
                if perms & QtCore.QFileDevice.WriteOwner == 0:
                    perms = perms | QtCore.QFileDevice.WriteOwner
                    QtCore.QFile.setPermissions(temp_path, perms)
                QtCore.QFile.remove(temp_path)
            if not QtCore.QFile.copy(f":/{license}", temp_path):
                QtWidgets.QMessageBox.critical(
                    self,
                    "Failed file copy",
                    f"Unable to copy the {license} to a temporary location for viewing",
                )
                return
            QtGui.QDesktopServices.openUrl(
                QtCore.QUrl(f"file:///{temp_path}", QtCore.QUrl.TolerantMode)
            )

    def is_recipe_active(self, uuid: QtCore.QUuid) -> bool:
        """
        Is the recipe with the given UUID active (i.e. has an open tab)?
        """
        mdi_area = self.centralWidget()
        return any(
            subwindow.widget().recipe.uuid == uuid
            for subwindow in mdi_area.subWindowList()
        )

    def _on_platform_theme_changed(self, color_scheme: QtCore.Qt.ColorScheme) -> None:
        if color_scheme == QtCore.Qt.ColorScheme.Unknown:
            color_scheme = QtCore.Qt.ColorScheme.Light
        cruiz.globals.CRUIZ_THEME = color_scheme.name
        self.theme_changed.emit(color_scheme.name)
