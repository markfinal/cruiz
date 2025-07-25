#!/usr/bin/env python3

"""Conan recipe widget representation."""

import logging
import os
import pathlib
import re
import typing

from PySide6 import QtCore, QtGui, QtWidgets

from attrs.converters import to_bool

import cruiz.globals
import cruiz.revealonfilesystem
import cruiz.workers.api as workers_api
from cruiz.commands.context import ConanContext
from cruiz.commands.logdetails import LogDetails
from cruiz.exceptions import RecipeInspectionError
from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.dependencygraph import dependencygraph_from_node_dependees
from cruiz.manage_local_cache import ManageLocalCachesDialog
from cruiz.model.graphaslistmodel import DependenciesListModel, DependenciesTreeModel
from cruiz.pyside6.recipe_window import Ui_RecipeWindow
from cruiz.revealonfilesystem import reveal_on_filesystem
from cruiz.settings.managers.basesettings import WorkflowCwd
from cruiz.settings.managers.fontpreferences import FontSettingsReader, FontUsage
from cruiz.settings.managers.generalpreferences import GeneralSettingsReader
from cruiz.settings.managers.namedlocalcache import NamedLocalCacheSettingsReader
from cruiz.settings.managers.recipe import (
    RecipeSettings,
    RecipeSettingsReader,
    RecipeSettingsWriter,
)
from cruiz.widgets.util import BlockSignals, clear_widgets_from_layout

try:
    import git
except ImportError as exc:
    print(exc)

from .dependencyview import InverseDependencyViewDialog
from .expressioneditordialog import ExpressionEditorDialog
from .findtextdialog import FindTextDialog
from .recipe import Recipe


logger = logging.getLogger(__name__)


class RecipeWidget(QtWidgets.QMainWindow):
    """Widget representing a Conan recipe."""

    configuration_changed = QtCore.Signal()
    local_workflow_changed = QtCore.Signal()

    def __init__(
        self,
        path: pathlib.Path,
        uuid: QtCore.QUuid,
        cache_name: str,
        parent: typing.Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Initialise a RecipeWidget."""
        super().__init__(parent)
        self._ui = Ui_RecipeWindow()
        self._ui.setupUi(self)  # type: ignore[no-untyped-call]
        try:
            self._git_repository: typing.Optional[git.Repo] = git.Repo(
                path, search_parent_directories=True
            )
        except NameError:
            self._git_repository = None
        except git.exc.InvalidGitRepositoryError:
            self._git_repository = None
        self._ui.paneSplitter.setStretchFactor(0, 4)
        self._ui.paneSplitter.setStretchFactor(1, 1)
        self._ui.outputPane.customContextMenuRequested.connect(self._pane_context_menu)
        self._ui.errorPane.customContextMenuRequested.connect(self._pane_context_menu)
        self._empty_widget = QtWidgets.QWidget(self)
        self._empty_widget.setFixedSize(0, 0)
        self._disable_delete_on_default_output_tab()
        self._ui.pane_tabs.tabCloseRequested.connect(self._on_tab_close_request)

        self._find_shortcut = QtGui.QShortcut(QtGui.QKeySequence("Ctrl+F"), self)
        self._find_shortcut.setContext(
            QtCore.Qt.ShortcutContext.WidgetWithChildrenShortcut
        )
        self._find_shortcut.activated.connect(self._open_find_dialog)
        with GeneralSettingsReader() as settings:
            combine_panes = settings.combine_panes.resolve()
            use_batching = settings.use_stdout_batching.resolve()
        self.combined_output_and_error_logs = combine_panes
        if self.combined_output_and_error_logs:
            self._ui.errorPane.hide()
        self._set_pane_font()
        self._ui.actionOpen_recipe_in_editor.triggered.connect(
            self._open_recipe_in_editor
        )
        self._ui.actionOpen_recipe_folder.triggered.connect(self._open_recipe_folder)
        self._ui.actionCopy_recipe_folder_to_clipboard.triggered.connect(
            self._copy_recipe_folder_to_clipboard
        )
        self._ui.actionOpen_another_version.triggered.connect(
            self._open_another_version
        )
        self._ui.actionManage_associated_local_cache.triggered.connect(
            self._manage_associated_local_cache
        )
        self._ui.actionReload.triggered.connect(self._reload)
        self._ui.actionClose.triggered.connect(self._close_recipe)
        self._ui.localWorkflowCwd.currentIndexChanged.connect(
            self._changed_local_workflow_cwd
        )
        self._ui.localWorkflowCwd.setItemData(0, WorkflowCwd.RELATIVE_TO_RECIPE)
        self._ui.localWorkflowCwd.setItemData(1, WorkflowCwd.RELATIVE_TO_GIT)
        if not self._git_repository:
            # if not a git repository, disable the option to use relative to git
            model = self._ui.localWorkflowCwd.model()
            assert isinstance(model, QtGui.QStandardItemModel)
            item = model.item(1)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEnabled)
        # TODO: need to fix this responsiveness
        # the QLineEdit.textChanged signal is not used here,
        # as the connected slots are so heavy weight that
        # user responsiveness on typing to the widgets is very bad
        # common subdir
        self._ui.localWorkflowCommonSubdir.editingFinished.connect(
            self._local_workflow_update_common_subdir
        )
        trash_icon = self.style().standardIcon(
            QtWidgets.QStyle.StandardPixmap.SP_TrashIcon
        )
        self._local_workflow_common_subdir_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_common_subdir_trash_action.setToolTip("Delete folder")
        self._local_workflow_common_subdir_trash_action.triggered.connect(
            self._local_workflow_on_delete_common_subdir
        )
        self._ui.localWorkflowCommonSubdir.addAction(
            self._local_workflow_common_subdir_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # install command
        self._ui.localWorkflowInstallFolder.editingFinished.connect(
            self._local_workflow_update_install_folder
        )
        self._local_workflow_install_folder_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_install_folder_trash_action.setToolTip("Delete folder")
        self._local_workflow_install_folder_trash_action.triggered.connect(
            self._local_workflow_on_delete_install_folder
        )
        self._ui.localWorkflowInstallFolder.addAction(
            self._local_workflow_install_folder_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # imports command
        self._ui.localWorkflowImportsFolder.editingFinished.connect(
            self._local_workflow_update_imports_folder
        )
        self._local_workflow_imports_folder_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_imports_folder_trash_action.setToolTip("Delete folder")
        self._local_workflow_imports_folder_trash_action.triggered.connect(
            self._local_workflow_on_delete_imports_folder
        )
        self._ui.localWorkflowImportsFolder.addAction(
            self._local_workflow_imports_folder_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # source command
        self._ui.localWorkflowSourceFolder.editingFinished.connect(
            self._local_workflow_update_source_folder
        )
        self._local_workflow_source_folder_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_source_folder_trash_action.setToolTip("Delete folder")
        self._local_workflow_source_folder_trash_action.triggered.connect(
            self._local_workflow_on_delete_source_folder
        )
        self._ui.localWorkflowSourceFolder.addAction(
            self._local_workflow_source_folder_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # build command
        self._ui.localWorkflowBuildFolder.editingFinished.connect(
            self._local_workflow_update_build_folder
        )
        self._local_workflow_build_folder_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_build_folder_trash_action.setToolTip("Delete folder")
        self._local_workflow_build_folder_trash_action.triggered.connect(
            self._local_workflow_on_delete_build_folder
        )
        self._ui.localWorkflowBuildFolder.addAction(
            self._local_workflow_build_folder_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # package command
        self._ui.localWorkflowPackageFolder.editingFinished.connect(
            self._local_workflow_update_package_folder
        )
        self._local_workflow_package_folder_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_package_folder_trash_action.setToolTip("Delete folder")
        self._local_workflow_package_folder_trash_action.triggered.connect(
            self._local_workflow_on_delete_package_folder
        )
        self._ui.localWorkflowPackageFolder.addAction(
            self._local_workflow_package_folder_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # test command
        self._ui.localWorkflowTestFolder.editingFinished.connect(
            self._local_workflow_update_test_folder
        )
        self._local_workflow_test_folder_trash_action = QtGui.QAction(
            trash_icon, "", self
        )
        self._local_workflow_test_folder_trash_action.setToolTip("Delete folder")
        self._local_workflow_test_folder_trash_action.triggered.connect(
            self._local_workflow_on_delete_test_folder
        )
        self._ui.localWorkflowTestFolder.addAction(
            self._local_workflow_test_folder_trash_action,
            QtWidgets.QLineEdit.ActionPosition.TrailingPosition,
        )
        # presets
        self._ui.localWorkflowClearAll.clicked.connect(self._local_workflow_clear_all)
        self._ui.localWorkflowCommonBuildFolder.clicked.connect(
            self._local_workflow_common_build_folder
        )
        self._ui.localWorkflowProfileAndVersionBasedSubdirs.clicked.connect(
            self._local_workflow_full_spec_folders
        )
        self._ui.localWorkflowExpressionEditor.clicked.connect(
            self._local_workflow_expression_editor
        )
        empty_regex = r"^$"
        pkgname_regex = r"[^:=,\s]+"
        option_name_regex = r"[^=,\s]+"
        option_value_regex = r"[^,\s]+"
        qualified_pkg_optionvalue = (
            f"{pkgname_regex}:{option_name_regex}={option_value_regex}"
        )
        comma_separated_regex = r"\s*,\s*"
        extra_option_list_regex = QtCore.QRegularExpression(
            # of the form <pkg>:<option>=<value>[,<repeat>]
            rf"{empty_regex}|^({qualified_pkg_optionvalue})({comma_separated_regex}{qualified_pkg_optionvalue})*$"  # noqa: E501
        )
        extra_option_list_validator = QtGui.QRegularExpressionValidator(
            extra_option_list_regex, self
        )
        self._ui.configureAdditionalOptions.setValidator(extra_option_list_validator)
        rgx = QtCore.QRegularExpression(r"(^$|^@([a-zA-Z_]+)\/([a-zA-Z_]+)$)")
        comValidator = QtGui.QRegularExpressionValidator(rgx, self)
        self._ui.configurePkgRefNamespace.setValidator(comValidator)
        self._ui.configurePkgRefNamespace.editingFinished.connect(
            self._configure_packageref_namespace
        )
        self._ui.configureAdditionalOptions.editingFinished.connect(
            self._configure_additional_options
        )
        self._ui.configurePackageId.customContextMenuRequested.connect(
            self._on_configure_packageid_context_menu
        )
        # tabify the docks on the right hand side
        self.tabifyDockWidget(
            self._ui.conanLocalWorkflowDock, self._ui.conanConfigureDock
        )
        # tabify the docks on the bottom side
        self.tabifyDockWidget(self._ui.conanLogDock, self._ui.conanCommandsDock)
        if cruiz.globals.CONAN_MAJOR_VERSION > 1:
            self._ui.conanLogDock.hide()
            self._ui.conanLocalWorkflowDock.hide()

        # dependency dock
        self._ui.dependentsTabs.setTabVisible(1, False)  # tree disabled
        self._ui.dependentsLog.hide()
        self._ui.dependentsLog.customContextMenuRequested.connect(
            self._dependents_log_context_menu
        )
        self._dependency_generate_log = LogDetails(
            self._ui.dependentsLog,
            None,
            True,
            False,
            None,
        )
        self._dependency_generate_context = ConanContext(
            cache_name, self._dependency_generate_log
        )
        self._dependency_generate_log.logging.connect(self._ui.dependentsLog.show)
        self._ui.dependency_rankdir.currentIndexChanged.connect(
            self._visualise_dependencies
        )

        # busy icon
        self._busy_icon = QtWidgets.QProgressBar(self)
        self._busy_icon.setTextVisible(False)
        self._busy_icon.setMinimum(0)
        self._busy_icon.setMaximum(1)

        # colours
        self._update_widget_colours_from_settings()

        # Git repository status label
        self._git_workspace_label = QtWidgets.QLabel(self)

        # signal connection
        self._ui.commandToolbar.command_started.connect(self._command_started)
        self._ui.commandToolbar.command_ended.connect(self._command_ended)
        self.configuration_changed.connect(
            self._on_configuration_update
        )  # note that this was seriously slow when using QLineEdit.textChanged signals
        self.local_workflow_changed.connect(self._on_local_workflow_update)
        self._ui.dependenciesPackageList.customContextMenuRequested.connect(
            self._dependency_list_context_menu
        )
        self._ui.behaviourToolbar.profile_changed.connect(
            self._generate_dependency_graph_from_profile_change
        )

        if cruiz.globals.CONAN_MAJOR_VERSION > 1:
            self._ui.buildFeaturesToolbar.hide()

        # associate with local caches
        self.log_details = LogDetails(
            self._ui.outputPane,
            self._ui.errorPane,
            self.combined_output_and_error_logs,
            use_batching,
            self._ui.conanLog,
        )
        self.log_details.start()
        self.recipe = Recipe(
            path,
            uuid,
            cache_name,
            self.log_details,
            self,
        )
        self.recipe.context.command_history_widget = self._ui.conanCommandHistory

        self._create_statusbar()
        self._load_local_workflow_dock()

        cruiz.globals.get_main_window().theme_changed.connect(self._on_theme_change)

    def post_init(self) -> None:
        """
        Post initialisation commands.

        These need to be performed once the recipe is visible, or that might fail
        (e.g. recipe syntax error)
        """
        attributes = self.get_recipe_attributes()
        self._update_window_title(attributes)
        self._update_toolbars(attributes)
        self._load_configuration_dock(attributes)
        self._generate_dependency_graph(attributes)

    @property
    def _are_commands_running(self) -> bool:
        return self.recipe.context.is_busy or self._dependency_generate_context.is_busy

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Override the widget's closeEvent."""
        if self._are_commands_running:
            QtWidgets.QMessageBox.warning(
                self,
                "Recipe cannot be closed",
                "Commands are still running. Cannot close recipe.",
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.NoButton,
            )
            event.ignore()
            return
        self._dependency_generate_log.stop()
        self._dependency_generate_context.close()
        self.log_details.stop()
        self.recipe.close()
        super().closeEvent(event)

    def get_recipe_attributes(
        self,
    ) -> typing.Dict[str, typing.Any]:
        """Get the attributes written into the recipe."""
        return self.recipe.context.inspect_recipe(
            self.recipe.path, propagate_errors=True
        )

    def _get_options_from_recipe(
        self, attrs: typing.Dict[str, typing.Any]
    ) -> typing.List[
        typing.Tuple[str, typing.Union[str, typing.List[typing.Any]], typing.Any]
    ]:
        # this lists the possible values for the option
        # in Conan 2, don't use the 'options' key, as that has been assigned the value
        options: typing.Optional[typing.Dict[str, typing.Any]] = (
            attrs.get("options")
            if cruiz.globals.CONAN_MAJOR_VERSION == 1
            else attrs.get("options_definitions")
        )
        if not options:
            return []
        default_options = attrs["default_options"]
        if isinstance(default_options, (tuple, list)):
            as_dict = {}
            for entry in default_options:
                key, value = entry.split("=")
                as_dict[key] = value
            default_options = as_dict
        assert isinstance(
            default_options, dict
        ), "Expected default_options to be a dict"
        values: typing.List[
            typing.Tuple[str, typing.Union[str, typing.List[typing.Any]], typing.Any]
        ] = []
        assert isinstance(options, dict)
        for key, value in options.items():
            if default_options:
                if cruiz.globals.CONAN_MAJOR_VERSION == 1:
                    default_value = default_options[key]
                else:
                    # when the recipe is serialised,
                    # default_options come through as typed (e.g. bool)
                    # while option_definitions are all strings, so in order to compare
                    # let's do everything as strings
                    default_value = str(default_options[key])
                if isinstance(value, list):
                    if default_value not in value and isinstance(value[0], bool):
                        default_value = to_bool(default_value)
                        assert default_value in value, (
                            f"Cannot find default value '{default_value}' in possible "
                            f"values {value}"
                        )
                elif (isinstance(value, str) and value == "ANY") or (
                    isinstance(value, list) and "ANY" in value
                ):
                    pass
                else:
                    raise TypeError(
                        f"Don't know how to convert '{default_value}' to type "
                        f"'{type(value[0])}'"
                    )
                values.append((key, value, default_value))
            else:
                values.append((key, value, None))
        return values

    # TODO: why does this have to be PurePosixPath? to create such a path,
    # it cannot be pure
    def get_working_dir(
        self,
        workflow_cwd: WorkflowCwd,
        common_subdir: typing.Optional[str],
    ) -> pathlib.PurePosixPath:
        """Get the working directory for the recipe."""
        if common_subdir is not None:
            common_subdir_path = pathlib.Path(common_subdir)
            if common_subdir_path.is_absolute():
                return pathlib.PurePosixPath(common_subdir_path)
        if workflow_cwd == WorkflowCwd.RELATIVE_TO_RECIPE:
            cwd = pathlib.PurePosixPath(self.recipe.folder)
        elif workflow_cwd == WorkflowCwd.RELATIVE_TO_GIT:
            assert self._git_repository
            assert self._git_repository.working_tree_dir
            cwd = pathlib.PurePosixPath(self._git_repository.working_tree_dir)
        if common_subdir is not None:
            cwd /= common_subdir
        return cwd

    def cwd_is_relative_to_recipe(self, workflow_cmd: WorkflowCwd) -> bool:
        """Is the current working directory relative to the recipe folder?."""
        if workflow_cmd == WorkflowCwd.RELATIVE_TO_RECIPE:
            return True
        return False

    def tokens(self) -> typing.Tuple[typing.Dict[str, str], str]:
        """Get a dict of tokens usable in expressions."""
        recipe_attributes = self.get_recipe_attributes()
        with RecipeSettingsReader.from_recipe(self.recipe) as settings_recipe:
            profile = settings_recipe.profile.resolve()
        profile_meta = self.recipe.context.get_profile_meta(profile)
        profile_path = pathlib.Path(profile)
        if profile_path.is_absolute():
            with NamedLocalCacheSettingsReader(
                self.recipe.context.cache_name
            ) as settings_localcache:
                extra_profile_dirs = (
                    settings_localcache.extra_profile_directories.resolve()
                )
            extra_profile_dir_name = [
                name
                for name, profile_dir in extra_profile_dirs.items()
                if pathlib.Path(profile).is_relative_to(pathlib.Path(profile_dir))
            ]
            assert (
                len(extra_profile_dir_name) == 1
            ), f"Unable to locate profile {profile} on extra dirs {extra_profile_dirs}"
            profile_prefix = f"{extra_profile_dir_name[0]}-"
        else:
            profile_prefix = ""

        tokens = {
            "name": recipe_attributes["name"],
            # version is either in the attributes, or for version agnostic recipes,
            # check the recipe object
            "version": recipe_attributes["version"] or self.recipe.version,
            "profile": f"{profile_prefix}{profile_path.name}",
            "build_type": profile_meta["settings"]["build_type"],
            "build_type_lc": profile_meta["settings"]["build_type"].lower(),
        }
        return tokens, r"(\${(.*?)})"

    def resolve_expression(
        self, expression: typing.Optional[str]
    ) -> typing.Optional[str]:
        """Resolve an expression using token expansion."""
        if not expression:
            return None
        tokens, token_regex = self.tokens()
        matches = re.findall(token_regex, expression)
        for match, token in matches:
            if token in tokens:
                expression = expression.replace(match, tokens[token])
            else:
                raise RuntimeError(
                    f"Unrecognised macro '{token}' found in '{expression}'"
                )
        return expression

    def _update_window_title(self, attributes: typing.Dict[str, str]) -> None:
        version_in_recipe = attributes.get("version")
        if version_in_recipe is not None:
            self._ui.actionOpen_another_version.setEnabled(False)
        version = version_in_recipe or self.recipe.version
        name = attributes.get("name")
        if self.recipe.user:
            package = f"{name}/{version}@{self.recipe.user}/{self.recipe.channel}"
        else:
            package = f"{name}/{version}"
        self.setWindowTitle(
            f"Package: {package} - Local cache: {self.recipe.context.cache_name}"
        )

    def _update_toolbars(
        self, attributes: typing.Dict[str, typing.Optional[str]]
    ) -> None:
        self._ui.behaviourToolbar.refresh_content()
        self._ui.buildFeaturesToolbar.refresh_content(self.recipe.uuid)
        try:
            self._ui.commandToolbar.configure_actions()  # this is a one off
            self._ui.commandToolbar.refresh_action_shortcuts_and_tooltips(attributes)
        except Exception as exc:
            logging.exception("Updating toolbars suppressed: '%s'", str(exc))
            self._ui.commandToolbar.disable_all_actions()

    def _create_statusbar(self) -> None:
        self._ui.statusbar.addWidget(self._busy_icon)
        if self._git_repository:
            self._git_workspace_label.setContextMenuPolicy(
                QtCore.Qt.ContextMenuPolicy.CustomContextMenu
            )
            self._git_workspace_label.customContextMenuRequested.connect(
                self._on_git_context_menu
            )
            self._ui.statusbar.addPermanentWidget(self._git_workspace_label)
        self._refresh_statusbar()

    def _refresh_statusbar(self) -> None:
        if self._git_repository:
            try:
                head_sha = self._git_repository.head.object.hexsha
                try:
                    branch = self._git_repository.active_branch
                    tracking_branch = branch.tracking_branch()
                    if tracking_branch is None:
                        tooltip = "Untracked branch"
                except TypeError:
                    branch = head_sha
                    tracking_branch = None
                    tooltip = "Detached head"
                message = f"{self._git_repository.working_tree_dir} " f"({branch})"
                if tracking_branch:
                    commits_behind = self._git_repository.iter_commits(
                        f"{branch}..{tracking_branch}"
                    )
                    num_commits_behind = sum(1 for _ in commits_behind)
                    tooltip = f"Tracking {tracking_branch}"
                    if num_commits_behind > 0:
                        message += f" \u2193{num_commits_behind}"
                        tooltip += f" {num_commits_behind} commits behind"
                    commits_ahead = self._git_repository.iter_commits(
                        f"{tracking_branch}..{branch}"
                    )
                    num_commits_ahead = sum(1 for _ in commits_ahead)
                    if num_commits_ahead > 0:
                        message += f" \u2191{num_commits_ahead}"
                        tooltip += f" {num_commits_ahead} commits ahead"
                    tooltip += f"\ncommit {head_sha}"

                self._git_workspace_label.setText(message)
                if tooltip:
                    self._git_workspace_label.setToolTip(tooltip)
            except (ValueError, git.exc.GitCommandError) as exc:
                logger.exception(exc)
                url = self._git_repository.remotes[0].url
                self._git_workspace_label.setText(
                    f"Unable to resolve details from {url}"
                )
                self._git_workspace_label.setToolTip(str(exc))

    def _on_git_context_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        fetch_action = QtGui.QAction("Fetch", self)
        fetch_action.triggered.connect(self._fetch_git_repository)
        menu.addAction(fetch_action)
        sender_widget = self.sender()
        assert isinstance(sender_widget, QtWidgets.QWidget)
        menu.exec_(sender_widget.mapToGlobal(position))

    def _fetch_git_repository(self) -> None:
        assert self._git_repository
        try:
            for remote in self._git_repository.remotes:
                remote.fetch()
            self._refresh_statusbar()
        except git.exc.GitCommandError as exc:
            logger.exception(exc)

    def on_preferences_update(self) -> None:
        """Slot called when preferences are updated."""
        attributes = self.get_recipe_attributes()
        self._ui.commandToolbar.refresh_action_shortcuts_and_tooltips(attributes)
        self._ui.buildFeaturesToolbar.refresh_content(self.recipe.uuid)
        self._set_pane_font()
        self._update_widget_colours_from_settings()

    def _on_local_workflow_update(self) -> None:
        attributes = self.get_recipe_attributes()
        self._ui.commandToolbar.refresh_action_shortcuts_and_tooltips(attributes)

    def _on_configuration_update(self) -> None:
        self._on_local_workflow_update()
        attributes = self.get_recipe_attributes()
        self._generate_dependency_graph(attributes)
        self._update_window_title(attributes)

    def _changed_local_workflow_cwd(self, index: int) -> None:
        settings = RecipeSettings()
        sender_combobox = self.sender()
        assert isinstance(sender_combobox, QtWidgets.QComboBox)
        settings.local_workflow_cwd = sender_combobox.itemData(index)
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()

    def _load_local_workflow_dock(self) -> None:
        with RecipeSettingsReader.from_recipe(self.recipe) as settings:
            workflow_cwd = settings.local_workflow_cwd.resolve()
            common_subdir = settings.local_workflow_common_subdir.resolve()
            install_folder = settings.local_workflow_install_folder.resolve()
            imports_folder = settings.local_workflow_imports_folder.resolve()
            source_folder = settings.local_workflow_source_folder.resolve()
            build_folder = settings.local_workflow_build_folder.resolve()
            package_folder = settings.local_workflow_package_folder.resolve()
            test_folder = settings.local_workflow_test_folder.resolve()

        # populate local workflow dock
        with BlockSignals(self._ui.localWorkflowCwd) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QComboBox)
            blocked_widget.setCurrentIndex(workflow_cwd)
        with BlockSignals(self._ui.localWorkflowCommonSubdir) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(common_subdir)
            self._local_workflow_common_subdir_trash_action.setEnabled(
                bool(common_subdir)
            )
        with BlockSignals(self._ui.localWorkflowInstallFolder) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(install_folder)
            self._local_workflow_install_folder_trash_action.setEnabled(
                bool(install_folder)
            )
        with BlockSignals(self._ui.localWorkflowImportsFolder) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(imports_folder)
            self._local_workflow_imports_folder_trash_action.setEnabled(
                bool(imports_folder)
            )
        with BlockSignals(self._ui.localWorkflowSourceFolder) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(source_folder)
            self._local_workflow_source_folder_trash_action.setEnabled(
                bool(source_folder)
            )
        with BlockSignals(self._ui.localWorkflowBuildFolder) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(build_folder)
            self._local_workflow_build_folder_trash_action.setEnabled(
                bool(build_folder)
            )
        with BlockSignals(self._ui.localWorkflowPackageFolder) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(package_folder)
            self._local_workflow_package_folder_trash_action.setEnabled(
                bool(package_folder)
            )
        with BlockSignals(self._ui.localWorkflowTestFolder) as blocked_widget:
            assert isinstance(blocked_widget, QtWidgets.QLineEdit)
            blocked_widget.setText(test_folder)
            self._local_workflow_test_folder_trash_action.setEnabled(bool(test_folder))

    def _load_configuration_dock(
        self, recipe_attributes: typing.Dict[str, str]
    ) -> None:
        with RecipeSettingsReader.from_recipe(self.recipe) as settings:
            options = settings.options.resolve()
            attributes = settings.attribute_overrides.resolve()
        if "user" in attributes:
            assert "channel" in attributes
            with BlockSignals(self._ui.configurePkgRefNamespace) as blocked_widget:
                assert isinstance(blocked_widget, QtWidgets.QLineEdit)
                blocked_widget.setText(f"@{attributes['user']}/{attributes['channel']}")
        if "extra_config_options" in attributes:
            with BlockSignals(self._ui.configureAdditionalOptions) as blocked_widget:
                assert isinstance(blocked_widget, QtWidgets.QLineEdit)
                blocked_widget.setText(attributes["extra_config_options"])
        clear_widgets_from_layout(self._ui.optionsLayout)
        recipe_options = self._get_options_from_recipe(recipe_attributes)
        for i, (key, values, default_value) in enumerate(recipe_options):
            self._ui.optionsLayout.addWidget(QtWidgets.QLabel(key), i, 0)
            if (isinstance(values, str) and values == "ANY") or (
                isinstance(values, list) and "ANY" in values
            ):
                value_edit = QtWidgets.QLineEdit()
                if key in options:
                    value_text = options[key]
                else:
                    if (
                        isinstance(values, list)
                        and None in values
                        and default_value is None
                    ):
                        value_text = "None (default)"
                    else:
                        value_text = f"{default_value} (default)"
                value_edit.setText(value_text)
                value_edit.setProperty("DefaultValue", default_value)
                value_edit.editingFinished.connect(self._option_any_changed)
                self._ui.optionsLayout.addWidget(value_edit, i, 1)
            else:
                assert isinstance(values, list)
                value_combo = QtWidgets.QComboBox()
                for j, value in enumerate(values):
                    if value == default_value:
                        value_combo.addItem(f"{value} (default)")
                    else:
                        value_combo.addItem(str(value))
                    value_combo.setItemData(j, value)
                if key in options:
                    # from options from QSettings, these are all strings and
                    # will never be the default value
                    current_index = value_combo.findText(options[key])
                else:
                    try:
                        current_index = values.index(default_value)
                    except ValueError:
                        current_index = -1
                value_combo.setCurrentIndex(current_index)
                value_combo.currentIndexChanged.connect(self._option_combo_changed)
                self._ui.optionsLayout.addWidget(value_combo, i, 1)
        self._ui.configureOptionsBox.setVisible(bool(recipe_options))

    def _option_any_changed(self) -> None:
        # divide by 2 as they are added in pairs
        widget = self.sender()
        assert isinstance(widget, QtWidgets.QLineEdit)
        index_of_option = self._ui.optionsLayout.indexOf(widget) // 2
        # get the label text (the option name)
        option_item = self._ui.optionsLayout.itemAtPosition(index_of_option, 0)
        assert option_item is not None
        option_label = option_item.widget()
        assert option_label is not None
        assert isinstance(option_label, QtWidgets.QLabel)
        name_of_option = option_label.text()
        settings = RecipeSettings()
        text = widget.text()
        default_value = widget.property("DefaultValue")
        if (
            text.endswith(" (default)")
            or (str(default_value) == text)
            or ((default_value is None and text.startswith("None")) or text == "")
        ):
            settings.append_options({name_of_option: None})  # type: ignore
            with BlockSignals(widget):
                widget.setText(f"{default_value} (default)")
        else:
            settings.append_options({name_of_option: text})  # type: ignore
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.configuration_changed.emit()

    def _option_combo_changed(self, index: int) -> None:
        # divide by 2 as they are added in pairs
        widget = self.sender()
        assert isinstance(widget, QtWidgets.QComboBox)
        index_of_option = self._ui.optionsLayout.indexOf(widget) // 2
        # get the label text (the option name)
        option_item = self._ui.optionsLayout.itemAtPosition(index_of_option, 0)
        assert option_item is not None
        option_label = option_item.widget()
        assert option_label is not None
        assert isinstance(option_label, QtWidgets.QLabel)
        name_of_option = option_label.text()
        option_value = widget.itemText(index)
        real_option_value = widget.itemData(index)
        settings = RecipeSettings()
        if option_value.endswith(" (default)"):
            settings.append_options({name_of_option: None})  # type: ignore
        else:
            settings.append_options(
                {name_of_option: str(real_option_value)}  # type: ignore
            )
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.configuration_changed.emit()

    def _local_workflow_update_common_subdir(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_common_subdir = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_common_subdir_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_update_install_folder(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_install_folder = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_install_folder_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_update_imports_folder(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_imports_folder = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_imports_folder_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_update_source_folder(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_source_folder = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_source_folder_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_update_build_folder(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_build_folder = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_build_folder_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_update_package_folder(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_package_folder = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_package_folder_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_update_test_folder(self) -> None:
        settings = RecipeSettings()
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        sender_text = sender_lineedit.text()
        settings.local_workflow_test_folder = sender_text
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()
        self._local_workflow_test_folder_trash_action.setEnabled(bool(sender_text))

    def _local_workflow_sync_dirs(self) -> None:
        # note that this is only necessary since we couldn't use the
        # QLineEdit.textChanged signal due to significant overhead
        settings = RecipeSettings()
        settings.local_workflow_common_subdir = (
            self._ui.localWorkflowCommonSubdir.text()
        )
        self._local_workflow_common_subdir_trash_action.setEnabled(
            bool(self._ui.localWorkflowCommonSubdir)
        )
        settings.local_workflow_install_folder = (
            self._ui.localWorkflowInstallFolder.text()
        )
        self._local_workflow_install_folder_trash_action.setEnabled(
            bool(self._ui.localWorkflowInstallFolder)
        )
        settings.local_workflow_imports_folder = (
            self._ui.localWorkflowImportsFolder.text()
        )
        self._local_workflow_imports_folder_trash_action.setEnabled(
            bool(self._ui.localWorkflowImportsFolder)
        )
        settings.local_workflow_source_folder = (
            self._ui.localWorkflowSourceFolder.text()
        )
        self._local_workflow_source_folder_trash_action.setEnabled(
            bool(self._ui.localWorkflowSourceFolder)
        )
        settings.local_workflow_build_folder = self._ui.localWorkflowBuildFolder.text()
        self._local_workflow_build_folder_trash_action.setEnabled(
            bool(self._ui.localWorkflowBuildFolder)
        )
        settings.local_workflow_package_folder = (
            self._ui.localWorkflowPackageFolder.text()
        )
        self._local_workflow_package_folder_trash_action.setEnabled(
            bool(self._ui.localWorkflowPackageFolder)
        )
        settings.local_workflow_test_folder = self._ui.localWorkflowTestFolder.text()
        self._local_workflow_test_folder_trash_action.setEnabled(
            bool(self._ui.localWorkflowTestFolder)
        )
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.local_workflow_changed.emit()

    def _local_workflow_on_delete_common_subdir(self) -> None:
        with RecipeSettingsReader.from_recipe(self.recipe) as settings:
            workflow_cwd = settings.local_workflow_cwd.resolve()
            common_subdir = settings.local_workflow_common_subdir.resolve()
        assert common_subdir
        working_dir = self.get_working_dir(workflow_cwd, common_subdir)
        # working_dir may be an expression so...
        resolved_working_dir = self.resolve_expression(os.fspath(working_dir))
        result = QtWidgets.QMessageBox.question(
            self,
            "Delete directory",
            f"Delete the directory '{resolved_working_dir}'?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.NoButton,
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return
        QtCore.QDir(resolved_working_dir).removeRecursively()

    def _local_workflow_on_delete_command_folder(self, property_name: str) -> None:
        with RecipeSettingsReader.from_recipe(self.recipe) as settings:
            workflow_cwd = settings.local_workflow_cwd.resolve()
            common_subdir = settings.local_workflow_common_subdir.resolve()
            command_subdir = getattr(settings, property_name).resolve()
        assert command_subdir
        command_subdir = pathlib.Path(command_subdir)
        if command_subdir.is_absolute():
            command_dir = command_subdir
        else:
            working_dir = self.get_working_dir(workflow_cwd, common_subdir)
            command_dir = pathlib.Path(working_dir) / command_subdir
        # command_dir may be an expression so...
        command_dir_str = self.resolve_expression(os.fspath(command_dir))
        result = QtWidgets.QMessageBox.question(
            self,
            "Delete directory",
            f"Delete the directory '{command_dir_str}'?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.NoButton,
        )
        if result == QtWidgets.QMessageBox.StandardButton.No:
            return
        QtCore.QDir(command_dir_str).removeRecursively()

    def _local_workflow_on_delete_install_folder(self) -> None:
        self._local_workflow_on_delete_command_folder("local_workflow_install_folder")

    def _local_workflow_on_delete_imports_folder(self) -> None:
        self._local_workflow_on_delete_command_folder("local_workflow_imports_folder")

    def _local_workflow_on_delete_source_folder(self) -> None:
        self._local_workflow_on_delete_command_folder("local_workflow_source_folder")

    def _local_workflow_on_delete_build_folder(self) -> None:
        self._local_workflow_on_delete_command_folder("local_workflow_build_folder")

    def _local_workflow_on_delete_package_folder(self) -> None:
        self._local_workflow_on_delete_command_folder("local_workflow_package_folder")

    def _local_workflow_on_delete_test_folder(self) -> None:
        self._local_workflow_on_delete_command_folder("local_workflow_test_folder")

    def _local_workflow_clear_all(self) -> None:
        self._ui.localWorkflowCommonSubdir.clear()
        self._ui.localWorkflowInstallFolder.clear()
        self._ui.localWorkflowImportsFolder.clear()
        self._ui.localWorkflowSourceFolder.clear()
        self._ui.localWorkflowBuildFolder.clear()
        self._ui.localWorkflowPackageFolder.clear()
        self._ui.localWorkflowTestFolder.clear()
        self._local_workflow_sync_dirs()

    def _local_workflow_common_build_folder(self) -> None:
        self._ui.localWorkflowCommonSubdir.setText("build")
        self._ui.localWorkflowInstallFolder.clear()
        self._ui.localWorkflowImportsFolder.clear()
        self._ui.localWorkflowSourceFolder.clear()
        self._ui.localWorkflowBuildFolder.clear()
        self._ui.localWorkflowPackageFolder.clear()
        self._ui.localWorkflowTestFolder.clear()
        self._local_workflow_sync_dirs()

    def _local_workflow_full_spec_folders(self) -> None:
        self._ui.localWorkflowCommonSubdir.setText("build")
        self._ui.localWorkflowInstallFolder.setText(
            "${name}/${version}/${profile}/install"
        )
        self._ui.localWorkflowImportsFolder.setText(
            "${name}/${version}/${profile}/imports"
        )
        self._ui.localWorkflowSourceFolder.setText("${name}/${version}/src")
        self._ui.localWorkflowBuildFolder.setText("${name}/${version}/${profile}/build")
        self._ui.localWorkflowPackageFolder.setText(
            "${name}/${version}/${profile}/package"
        )
        self._ui.localWorkflowTestFolder.setText("${name}/${version}/${profile}/test")
        self._local_workflow_sync_dirs()

    def _local_workflow_expression_editor(self) -> None:
        ExpressionEditorDialog(self).exec_()

    def _configure_packageref_namespace(self) -> None:
        # Note: this does appear to get called twice, which also appears to be a bug
        # https://stackoverflow.com/questions/26782211/qlineedit-editingfinished-signal-twice-when-changing-focus
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        text = sender_lineedit.text()
        settings = RecipeSettings()
        if text:
            validator = sender_lineedit.validator()
            assert isinstance(validator, QtGui.QRegularExpressionValidator)
            regex = validator.regularExpression()
            matches = regex.match(text)
            assert matches.lastCapturedIndex() == 3
            user = matches.captured(2)
            channel = matches.captured(3)
            settings.append_attribute(
                {"user": user, "channel": channel}  # type: ignore
            )
        else:
            settings.append_attribute({"user": None, "channel": None})  # type: ignore
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.configuration_changed.emit()

    def _configure_additional_options(self) -> None:
        sender_lineedit = self.sender()
        assert isinstance(sender_lineedit, QtWidgets.QLineEdit)
        text = sender_lineedit.text()
        settings = RecipeSettings()
        if text:
            settings.append_attribute({"extra_config_options": text})  # type: ignore
        else:
            settings.append_attribute({"extra_config_options": None})  # type: ignore
        RecipeSettingsWriter.from_recipe(self.recipe).sync(settings)
        self.configuration_changed.emit()

    def _open_recipe_in_editor(self) -> None:
        # TODO: make the editor a preference
        with GeneralSettingsReader() as settings:
            recipe_editor = settings.default_recipe_editor.resolve()
        if recipe_editor:
            script_args = [str(self.recipe.path)]
            QtCore.QProcess.execute(recipe_editor, script_args)
        else:
            url = QtCore.QUrl.fromLocalFile(str(self.recipe.path))
            QtGui.QDesktopServices.openUrl(url)

    def _open_recipe_folder(self) -> None:
        reveal_on_filesystem(self.recipe.folder)

    def _copy_recipe_folder_to_clipboard(self) -> None:
        QtWidgets.QApplication.clipboard().setText(str(self.recipe.folder))

    def _open_another_version(self) -> None:
        # TODO: note the last argument to this is the wrong type
        cruiz.globals.get_main_window().load_recipe(self.recipe.path, None, self)

    def _manage_associated_local_cache(self) -> None:
        dialog = ManageLocalCachesDialog(self, self.recipe.context.cache_name)
        dialog.cache_changed.connect(self.on_local_cache_changed)
        dialog.exec_()

    def _generate_dependency_graph_from_profile_change(self, profile: str) -> None:
        # pylint: disable=unused-argument
        attributes = self.get_recipe_attributes()
        self._generate_dependency_graph(attributes)

    def _generate_dependency_graph(
        self, recipe_attributes: typing.Dict[str, str]
    ) -> None:
        # reset views
        self._ui.configurePackageId.setText("Calculating...")
        # https://stackoverflow.com/questions/46630185/qt-remove-model-from-view
        self._ui.dependenciesPackageList.setModel(None)
        self._ui.dependencyView.clear()
        # calculate lock file
        params = CommandParameters("lock create", workers_api.lockcreate.invoke)
        params.recipe_path = self.recipe.path
        params.name = recipe_attributes.get("name")
        params.version = self.recipe.version
        params.user = self.recipe.user
        params.channel = self.recipe.channel
        with RecipeSettingsReader.from_recipe(self.recipe) as settings:
            params.profile = settings.profile.resolve()
            for key, value in settings.options.resolve().items():
                # TODO: is this the most efficient algorithm?
                params.add_option(params.name, key, value)
            attributes = settings.attribute_overrides.resolve()
            if "extra_config_options" in attributes:
                for keyvalue in attributes["extra_config_options"].split(","):
                    option_name, option_value = keyvalue.split("=", maxsplit=1)
                    params.add_option(None, option_name, option_value)
        self._dependency_generate_context.conancommand(
            params,
            None,
            self._on_dependency_graph_generated,
        )

    def _on_dependency_graph_generated(
        self, payload: typing.Any, exception: typing.Any
    ) -> None:
        if payload:
            self.dependency_graph = payload
            self._ui.configurePackageId.setText(self.dependency_graph.root.package_id)
            try:
                self._visualise_dependencies(self._ui.dependency_rankdir.currentIndex())
            except FileNotFoundError as exc:
                exception = exc
                # fall through
        if exception:
            if payload is None:
                self._ui.configurePackageId.setText("Failed")
                self.dependency_graph = None
            lines = str(exception).splitlines()
            html = ""
            for line in lines:
                stripped_line = line.lstrip()
                num_leading_spaces = len(line) - len(stripped_line)
                html += "&nbsp;" * num_leading_spaces + stripped_line + "<br>"
            self._dependency_generate_log.stderr(
                f"Exception raised from running command:<br>"
                f"<font color='red'>{html}</font><br>"
            )

    def _visualise_dependencies(self, rank_dir_index: int) -> None:
        if self.dependency_graph is None:
            return
        # list visualisation of dependencies
        self._dependencies_list_model = DependenciesListModel(self.dependency_graph)
        self._ui.dependenciesPackageList.setModel(self._dependencies_list_model)
        # tree visualisation of dependencies (DISABLED)
        self._dependencies_tree_model = DependenciesTreeModel(self.dependency_graph)
        self._ui.dependenciesPackageTree.setModel(self._dependencies_tree_model)
        # graphical visualisation of dependencies
        self._ui.dependencyView.visualise(self.dependency_graph, rank_dir_index)

    def _set_pane_font(self) -> None:
        with FontSettingsReader(FontUsage.OUTPUT) as settings:
            name = settings.name.resolve()
            size = settings.size.resolve()
        if name:
            font = QtGui.QFont(name, size)
        else:
            font = QtGui.QFontDatabase.systemFont(
                QtGui.QFontDatabase.SystemFont.FixedFont
            )
        for i in range(self._ui.pane_tabs.count()):
            tab_widget = self._ui.pane_tabs.widget(i)
            splitter = (
                tab_widget
                if isinstance(tab_widget, QtWidgets.QSplitter)
                else tab_widget.findChild(QtWidgets.QSplitter)
            )
            assert splitter is not None
            left_widget = splitter.widget(0)
            assert isinstance(left_widget, QtWidgets.QPlainTextEdit)
            left_widget.document().setDefaultFont(font)
            right_widget = splitter.widget(1)
            assert isinstance(right_widget, QtWidgets.QPlainTextEdit)
            right_widget.document().setDefaultFont(font)

    def failed_to_load(self) -> None:
        """Call this in a recipe failure to load situation, that disables everything."""
        self._ui.conanDependencyDock.setEnabled(False)
        self._ui.conanCommandsDock.setEnabled(False)
        self._ui.conanCommandHistory.setEnabled(False)
        self._ui.conanConfigureDock.setEnabled(False)
        self._ui.conanLocalWorkflowDock.setEnabled(False)
        self._ui.behaviourToolbar.setEnabled(False)
        self._ui.buildFeaturesToolbar.setEnabled(False)
        self._ui.commandToolbar.disable_all_actions()
        self.setWindowTitle(f"Failed to load recipe {self.recipe.path}")
        # ensure that toolbar icons are loaded, even if the tooltips are wrong
        self._update_toolbars({})

    def _command_started(self) -> None:
        self._busy_icon.setMaximum(0)
        self._ui.conanConfigureDock.setEnabled(False)
        self._ui.conanLocalWorkflowDock.setEnabled(False)
        self._ui.behaviourToolbar.setEnabled(False)
        self._ui.buildFeaturesToolbar.setEnabled(False)

    def _command_ended(self) -> None:
        self._busy_icon.setMaximum(1)
        self._ui.conanConfigureDock.setEnabled(True)
        self._ui.conanLocalWorkflowDock.setEnabled(True)
        self._ui.behaviourToolbar.setEnabled(True)
        self._ui.buildFeaturesToolbar.setEnabled(True)

    def _pane_context_menu(self, position: QtCore.QPoint) -> None:
        sender_plaintextedit = self.sender()
        assert isinstance(sender_plaintextedit, QtWidgets.QPlainTextEdit)
        menu = sender_plaintextedit.createStandardContextMenu(position)
        menu.addSeparator()
        find_action = QtGui.QAction("Find...", self)
        find_action.setShortcut(self._find_shortcut.key())
        find_action.setShortcutVisibleInContextMenu(True)
        find_action.setData(sender_plaintextedit)
        find_action.triggered.connect(self._open_find_dialog)
        menu.addAction(find_action)
        menu.addSeparator()
        clear_action = QtGui.QAction("Clear", self)
        clear_action.triggered.connect(sender_plaintextedit.clear)
        menu.addAction(clear_action)
        menu.addSeparator()
        pin_action = QtGui.QAction("Pin to tab", self)
        pin_action.triggered.connect(self._pin_current_output)
        pin_action.setEnabled(self._ui.pane_tabs.count() == 1)
        menu.addAction(pin_action)
        menu.exec_(sender_plaintextedit.viewport().mapToGlobal(position))

    def _open_find_dialog(self) -> None:
        if isinstance(self.sender(), QtGui.QShortcut):
            pane = QtWidgets.QApplication.focusWidget()
        else:
            sender_action = self.sender()
            assert isinstance(sender_action, QtGui.QAction)
            pane = sender_action.data()
        if isinstance(pane, QtWidgets.QPlainTextEdit):
            dialog = FindTextDialog(pane)
            dialog.search_forwards.connect(self._find_next)
            dialog.search_backwards.connect(self._find_prev)
            dialog.exec_()

    def _find_next(
        self,
        pane: QtWidgets.QPlainTextEdit,
        pattern: str,
        case_sensitive: bool,
        wrap_around: bool,
    ) -> None:
        if case_sensitive:
            result = pane.find(
                pattern, QtGui.QTextDocument.FindFlag.FindCaseSensitively
            )
        else:
            result = pane.find(pattern)
        if not result and wrap_around:
            pane.moveCursor(QtGui.QTextCursor.MoveOperation.Start)
            if case_sensitive:
                result = pane.find(
                    pattern, QtGui.QTextDocument.FindFlag.FindCaseSensitively
                )
            else:
                result = pane.find(pattern)

    def _find_prev(
        self,
        pane: QtWidgets.QPlainTextEdit,
        pattern: str,
        case_sensitive: bool,
        wrap_around: bool,
    ) -> None:
        flags = QtGui.QTextDocument.FindFlag.FindBackward
        if case_sensitive:
            flags |= QtGui.QTextDocument.FindFlag.FindCaseSensitively
        result = pane.find(pattern, flags)
        if not result and wrap_around:
            pane.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            result = pane.find(pattern, flags)

    def _dependency_list_context_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        open_package_dir_action = QtGui.QAction("Open package directory", self)
        open_package_dir_action.triggered.connect(self._open_package_directory)
        menu.addAction(open_package_dir_action)
        copy_package_dir_action = QtGui.QAction(
            "Copy package directory to clipboard", self
        )
        copy_package_dir_action.triggered.connect(self._copy_package_directory)
        menu.addAction(copy_package_dir_action)
        what_uses_this_action = QtGui.QAction("What uses this?...", self)
        what_uses_this_action.triggered.connect(self._on_what_uses_this)
        menu.addAction(what_uses_this_action)
        menu.exec_(self._ui.dependenciesPackageList.mapToGlobal(position))

    def _get_package_directory_of_current_dependency(self) -> pathlib.Path:
        index = self._ui.dependenciesPackageList.currentIndex()
        node = index.data(QtCore.Qt.ItemDataRole.UserRole)
        return self.recipe.context.get_package_directory(node)

    def _open_package_directory(self) -> None:
        directory = self._get_package_directory_of_current_dependency()
        if directory.is_dir():
            cruiz.revealonfilesystem.reveal_on_filesystem(directory)
        else:
            QtWidgets.QMessageBox.critical(
                self,
                "No such package directory",
                f"Package directory '{directory}' does not exist",
                QtWidgets.QMessageBox.StandardButton.Ok,
                QtWidgets.QMessageBox.StandardButton.NoButton,
            )

    def _copy_package_directory(self) -> None:
        directory = self._get_package_directory_of_current_dependency()
        QtWidgets.QApplication.clipboard().setText(os.fspath(directory))

    def _on_what_uses_this(self) -> None:
        index = self._ui.dependenciesPackageList.currentIndex()
        node = index.data(QtCore.Qt.ItemDataRole.UserRole)
        new_graph = dependencygraph_from_node_dependees(node)
        InverseDependencyViewDialog(new_graph).exec_()

    def _dependents_log_context_menu(self, position: QtCore.QPoint) -> None:
        sender_plaintextedit = self.sender()
        assert isinstance(sender_plaintextedit, QtWidgets.QPlainTextEdit)
        menu = sender_plaintextedit.createStandardContextMenu(position)
        menu.addSeparator()
        clear_action = QtGui.QAction("Clear", self)
        clear_action.triggered.connect(self._clear_dependents_log)
        menu.addAction(clear_action)
        menu.exec_(sender_plaintextedit.viewport().mapToGlobal(position))

    def _clear_dependents_log(self) -> None:
        self._ui.dependentsLog.clear()
        self._ui.dependentsLog.hide()

    def _update_widget_colours_from_settings(self) -> None:
        def _set_widget_highlight_colour(
            widget: QtWidgets.QWidget, colour: QtGui.QColor
        ) -> None:
            palette = widget.palette()
            palette.setColor(QtGui.QPalette.ColorRole.Highlight, colour)
            widget.setPalette(palette)

        with GeneralSettingsReader() as settings:
            busy_icon_color = settings.busy_icon_colour.resolve()
            found_text_background_color = (
                settings.found_text_background_colour.resolve()
            )

        colour = (
            f"{busy_icon_color.red()}, "
            f"{busy_icon_color.green()}, "
            f"{busy_icon_color.blue()}"
        )
        style = (
            "QProgressBar::chunk "
            f"{{background-color: rgb({colour}); width: 5px; margin: 2.5px;}}"
        )
        self._busy_icon.setStyleSheet(style)

        _set_widget_highlight_colour(self._ui.outputPane, found_text_background_color)
        _set_widget_highlight_colour(self._ui.errorPane, found_text_background_color)

    def _pin_current_output(self) -> None:
        # create a pinned readonly copy of the current output for inspection
        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical, self)
        output = QtWidgets.QPlainTextEdit()
        output.appendHtml(self._ui.outputPane.document().toHtml())
        error = QtWidgets.QPlainTextEdit()
        error.appendHtml(self._ui.errorPane.document().toHtml())
        splitter.addWidget(output)
        splitter.addWidget(error)
        with GeneralSettingsReader() as settings:
            if settings.combine_panes.resolve():
                error.hide()
        self._ui.pane_tabs.addTab(splitter, "Pinned output")
        self._set_pane_font()

    def _disable_delete_on_default_output_tab(self) -> None:
        # default tab containing the output pane is not closable (but others are)
        self._ui.pane_tabs.tabBar().setTabButton(
            0, QtWidgets.QTabBar.ButtonPosition.LeftSide, self._empty_widget
        )
        self._ui.pane_tabs.tabBar().setTabButton(
            0, QtWidgets.QTabBar.ButtonPosition.RightSide, self._empty_widget
        )

    def _on_tab_close_request(self, index: int) -> None:
        self._ui.pane_tabs.removeTab(index)

    def _reload(self) -> None:
        self._ui.outputPane.clear()
        self._ui.errorPane.clear()
        self._load_local_workflow_dock()
        try:
            attributes = self.get_recipe_attributes()
        except RecipeInspectionError:
            # this error has already been posted to the log window
            self.failed_to_load()
            return
        self._update_window_title(attributes)
        self._load_configuration_dock(attributes)
        self._generate_dependency_graph(attributes)

    def _close_recipe(self) -> None:
        sub_window = self.parent()
        assert isinstance(sub_window, QtWidgets.QMdiSubWindow)
        sub_window.close()

    def on_local_cache_changed(self, cache_name: str) -> None:
        """Slot called when a local cache is changed so that user facing information can be updated."""  # noqa: E501
        if cache_name != self.recipe.context.cache_name:
            return
        self._ui.behaviourToolbar.refresh_content()

    def _on_configure_packageid_context_menu(self, position: QtCore.QPoint) -> None:
        action = QtGui.QAction("Copy to clipboard", self)
        action.triggered.connect(self._on_configure_package_id_copy)
        menu = QtWidgets.QMenu(self)
        menu.addAction(action)
        sender_label = self.sender()
        assert isinstance(sender_label, QtWidgets.QLabel)
        menu.exec_(sender_label.mapToGlobal(position))

    def _on_configure_package_id_copy(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._ui.configurePackageId.text())

    def _on_theme_change(self) -> None:
        attributes = self.get_recipe_attributes()
        self._ui.commandToolbar.refresh_action_shortcuts_and_tooltips(attributes)
