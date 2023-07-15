#!/usr/bin/env python3

"""
Remote browser page
"""

import typing

from qtpy import QtCore, QtGui, QtWidgets

from cruiz.interop.packageidparameters import PackageIdParameters
from cruiz.widgets.util import BlockSignals

from .page import Page


class _PackageIdModel(QtCore.QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._pids: typing.Optional[
            typing.List[
                typing.Dict[
                    str,
                    typing.Union[str, bool, typing.Dict[str, str], typing.List[str]],
                ]
            ]
        ] = None
        self._options: typing.Optional[typing.List[str]] = None
        self._settings: typing.Optional[typing.List[str]] = None
        self._options_values: typing.Optional[typing.Dict[str, typing.Set[str]]] = None
        self._settings_values: typing.Optional[typing.Dict[str, typing.Set[str]]] = None

    def set(
        self,
        results: typing.Optional[
            typing.List[
                typing.Dict[
                    str,
                    typing.Union[str, bool, typing.Dict[str, str], typing.List[str]],
                ]
            ]
        ],
    ) -> None:
        """
        Set the package ids into the model
        """
        self.beginResetModel()
        self._pids = results
        if results is not None:
            options = set()
            option_values: typing.Dict[str, typing.Set[str]] = {}
            settings = set()
            settings_values: typing.Dict[str, typing.Set[str]] = {}
            for pid in results:
                if "options" in pid:
                    assert isinstance(pid["options"], dict)
                    for option, value in pid["options"].items():
                        options.add(option)
                        if option not in option_values:
                            option_values[option] = set()
                        option_values[option].add(value)
                if "settings" in pid:
                    assert isinstance(pid["settings"], dict)
                    for setting, value in pid["settings"].items():
                        settings.add(setting)
                        if setting not in settings_values:
                            settings_values[setting] = set()
                        settings_values[setting].add(value)
            self._options = sorted(list(options))
            self._settings = sorted(list(settings))
            self._options_values = option_values
            self._settings_values = settings_values
        else:
            self._options = None
            self._settings = None
            self._options_values = None
            self._settings_values = None
        self.endResetModel()

    def rowCount(self, parent) -> int:  # type: ignore
        if parent.isValid():
            return 0
        if self._pids is None:
            return 0
        return len(self._pids)

    def columnCount(self, parent) -> int:  # type: ignore
        # pylint: disable=unused-argument
        if self._pids is None:
            return 0
        num_cols = 1  # the package id
        if self._settings:
            num_cols += len(self._settings)
        if self._options:
            num_cols += len(self._options)
        if "requires" in self._pids[0]:
            num_cols += 1
        return num_cols

    def headerData(self, section, orientation, role):  # type: ignore
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            num_settings = len(self._settings) if self._settings else 0
            num_options = len(self._options) if self._options else 0
            if section == 0:
                return "Package Id"
            if section >= 1 and section < 1 + num_settings:
                return self._settings[section - 1]  # type: ignore[index]
            if section >= 1 + num_settings and section < 1 + num_settings + num_options:
                index = section - 1 - num_settings
                return self._options[index]  # type: ignore[index]
            return "Requires"
        return None

    def data(self, index, role):  # type: ignore
        if role == QtCore.Qt.DisplayRole:
            num_settings = len(self._settings) if self._settings else 0
            num_options = len(self._options) if self._options else 0
            section = index.column()
            assert self._pids
            if section == 0:
                return self._pids[index.row()]["id"]
            if section >= 1 and section < 1 + num_settings:
                header = self.headerData(  # type: ignore[no-untyped-call]
                    section, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole
                )
                try:
                    return self._pids[index.row()]["settings"][header]
                except KeyError:
                    return "-"
            if section >= 1 + num_settings and section < 1 + num_settings + num_options:
                header = self.headerData(  # type: ignore[no-untyped-call]
                    section, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole
                )
                try:
                    return self._pids[index.row()]["options"][header]
                except KeyError:
                    return "-"
            value = "\n".join(sorted(self._pids[index.row()]["requires"]))
            return value
        return None


class _FilteringModel(QtCore.QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._filters: typing.List[typing.Tuple[int, str, str]] = []

    def add(self, index: int, key: str, value: str) -> None:
        self.beginResetModel()
        self._filters.append((index, key, value))
        self.endResetModel()

    def remove(self, index: int) -> None:
        self.beginResetModel()
        del self._filters[index]
        self.endResetModel()

    def invalidate(self) -> None:
        self.beginResetModel()
        self._filters = []
        self.endResetModel()

    def rowCount(self, parent) -> int:  # type: ignore
        return len(self._filters)

    def columnCount(self, parent) -> int:  # type: ignore
        return 2

    def data(self, index, role):  # type: ignore
        if role == QtCore.Qt.DisplayRole:
            return self._filters[index.row()][index.column() + 1]
        return None

    def headerData(self, section, orientation, role):  # type: ignore
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return "Key"
            return "Value"
        return None


class _PackageIdSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, model: _PackageIdModel, filtering: _FilteringModel) -> None:
        super().__init__()
        self.setSourceModel(model)
        self._filtering = filtering

    def filterAcceptsRow(
        self,
        source_row: int,
        source_parent: typing.Union[QtCore.QModelIndex, QtCore.QPersistentModelIndex],
    ) -> bool:
        for column, _, value in self._filtering._filters:
            index = self.sourceModel().index(source_row, column, source_parent)
            if value != self.sourceModel().data(
                index, QtCore.Qt.DisplayRole  # type: ignore
            ):
                return False
        return super().filterAcceptsRow(source_row, source_parent)


class PackageIdPage(Page):
    """
    Remote browser page for displaying package ids
    """

    def setup(self, self_ui: typing.Any) -> None:
        """
        Setup the UI for the page
        """
        self._base_setup(self_ui, 2)
        self._current_pkgref: typing.Optional[str] = None
        self._model = _PackageIdModel()
        self._filtering_model = _FilteringModel()
        self._sorting_model = _PackageIdSortFilterProxyModel(
            self._model, self._filtering_model
        )
        self._ui.package_ids.setModel(self._sorting_model)
        self._ui.package_ids.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self._ui.package_ids.horizontalHeader().setContextMenuPolicy(
            QtCore.Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._ui.package_ids.horizontalHeader().customContextMenuRequested.connect(
            self._on_package_id_header_menu
        )
        self._ui.package_ids.verticalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self._ui.package_ids.customContextMenuRequested.connect(
            self._on_selected_pkgref_menu
        )

        self._ui.package_ids.doubleClicked.connect(self._on_pid_dclicked)
        self._ui.pid_back.clicked.connect(self._on_back)
        self._ui.pid_cancel.clicked.connect(self.on_cancel)
        self._ui.pid_refresh.clicked.connect(self._on_refresh)
        self._ui.pid_restart.clicked.connect(self._on_restart)
        self._ui.pid_pkgref.customContextMenuRequested.connect(self._on_pkgref_menu)
        self._ui.pid_filterTable.setModel(self._filtering_model)
        self._ui.pid_filterTable.customContextMenuRequested.connect(
            self._on_pid_filter_menu
        )
        self._ui.pid_filter_key.currentTextChanged.connect(self._on_pid_filter_changed)
        self._ui.pid_filter_value.currentTextChanged.connect(
            self._on_pid_filter_value_changed
        )
        self._ui.pid_add_filter.clicked.connect(self._on_add_pid_filter)

    @property
    def package_reference(self) -> str:
        """
        Get the package reference selected in the current page
        """
        selection = self._ui.package_ids.selectedIndexes()
        assert (
            len(selection) > 0
        )  # hard to determine the number, but it's only the first we want
        package_id = self._sorting_model.data(
            selection[0], QtCore.Qt.DisplayRole  # type: ignore
        )
        return f"{self._previous_pkgref}:{package_id}"

    def _enable_progress(self, enable: bool) -> None:
        self._ui.pid_progress.setMaximum(0 if enable else 1)
        self._ui.pid_buttons.setEnabled(not enable)
        self._ui.pid_cancel.setEnabled(enable)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        # pylint: disable=unused-argument
        self._ui.pid_pkgref.setText(self._previous_pkgref)
        self._compute()

    def _complete(self, results: typing.Any, exception: typing.Any) -> None:
        self._enable_progress(False)
        if exception:
            self._ui.pid_groupbox.setTitle("Error finding package ids")
            self._log_details.stderr(str(exception))
            return
        if results is not None:
            self._model.set(results)
            self._ui.pid_groupbox.setTitle(f"{len(results)} package ids found")
            self._ui.pid_groupbox.setEnabled(True)
            self._current_pkgref = self._previous_pkgref
            self._ui.pid_filter_group.setEnabled(True)
            self._populate_settings_options_filter()

    def _populate_settings_options_filter(self) -> None:
        self._ui.pid_filter_value.setEnabled(False)
        self._ui.pid_add_filter.setEnabled(False)
        # brute force re-add all the settings and options
        with BlockSignals(self._ui.pid_filter_key) as blocked_widget:
            blocked_widget.clear()
            blocked_widget.addItem("Package Id")
            blocked_widget.addItems(self._model._settings)
            blocked_widget.addItems(self._model._options)
            blocked_widget.setCurrentIndex(-1)
        model = self._ui.pid_filter_key.model()
        # disable those with active filters
        for index, _, _ in self._filtering_model._filters:
            item = model.item(index)
            item.setEnabled(False)
        with BlockSignals(self._ui.pid_filter_value) as blocked_widget:
            blocked_widget.clear()
            blocked_widget.setCurrentIndex(-1)

    def _on_back(self) -> None:
        if self._revisions_enabled:
            self._open_previous_page()
        else:
            # skip recipe revisions
            self.parent().setCurrentIndex(self.page_index - 2)

    def _on_pid_dclicked(self, index: QtCore.QModelIndex) -> None:
        # pylint: disable=unused-argument
        if self._revisions_enabled:
            self._open_next_page()
        else:
            # skip package revisions
            self.parent().setCurrentIndex(self.page_index + 2)

    def on_cancel(self) -> None:
        """
        Called when the user cancels the operation.
        """
        self._context.cancel()
        self._enable_progress(False)

    def _on_refresh(self) -> None:
        self._current_pkgref = None
        self._compute()

    def _compute(self) -> None:
        pkgref = self._previous_pkgref
        if self._current_pkgref != pkgref:
            self._ui.pid_groupbox.setTitle("0 package ids found")
            self._model.set(None)
            self._enable_progress(True)
            self._ui.pid_groupbox.setEnabled(False)
            self._ui.pid_filter_group.setEnabled(False)
            params = PackageIdParameters(
                reference=pkgref,
                remote_name=self._ui.remote.currentText(),
            )
            self._context.get_package_details(params, self._complete)

    def _on_restart(self) -> None:
        self._filtering_model.invalidate()
        self._sorting_model.invalidateFilter()
        self._open_start()

    def _on_copy_pkgref_to_clip(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._ui.pid_pkgref.text())

    def _on_package_id_header_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        offset = 1
        assert self._model._settings
        for i, s in enumerate(self._model._settings):
            action = QtGui.QAction(s, self)
            action.setCheckable(True)
            action.setData(i + offset)
            action.setChecked(not self._ui.package_ids.isColumnHidden(i + offset))
            action.toggled.connect(self._on_toggle_hide_column)
            menu.addAction(action)
        menu.addSeparator()
        offset = 1 + len(self._model._settings)
        assert self._model._options
        for i, o in enumerate(self._model._options):
            action = QtGui.QAction(o, self)
            action.setData(i + offset)
            action.setCheckable(True)
            action.setChecked(not self._ui.package_ids.isColumnHidden(i + offset))
            action.toggled.connect(self._on_toggle_hide_column)
            menu.addAction(action)
        menu.addSeparator()
        offset = 1 + len(self._model._settings) + len(self._model._options)
        action = QtGui.QAction("Requires", self)
        action.setData(offset)
        action.setCheckable(True)
        action.setChecked(not self._ui.package_ids.isColumnHidden(offset))
        action.toggled.connect(self._on_toggle_hide_column)
        menu.addAction(action)
        menu.exec_(self.sender().mapToGlobal(position))

    def _on_toggle_hide_column(self, checked: bool) -> None:
        action = self.sender()
        self._ui.package_ids.setColumnHidden(action.data(), not checked)

    def _on_pid_filter_changed(self, text: str) -> None:
        self._ui.pid_filter_value.setEnabled(True)
        assert self._model._settings
        if self.sender().currentIndex() == 0:
            with BlockSignals(self._ui.pid_filter_value) as blocked_widget:
                blocked_widget.clear()
                assert self._model._pids
                for pid in self._model._pids:
                    blocked_widget.addItem(pid["id"])
                blocked_widget.setCurrentIndex(-1)
        elif self.sender().currentIndex() < len(self._model._settings) + 1:
            with BlockSignals(self._ui.pid_filter_value) as blocked_widget:
                blocked_widget.clear()
                assert self._model._settings_values
                blocked_widget.addItems(self._model._settings_values[text])
                blocked_widget.setCurrentIndex(-1)
        else:
            with BlockSignals(self._ui.pid_filter_value) as blocked_widget:
                blocked_widget.clear()
                assert self._model._options_values
                blocked_widget.addItems(self._model._options_values[text])
                blocked_widget.setCurrentIndex(-1)

    def _on_pid_filter_value_changed(self, text: str) -> None:
        self._ui.pid_add_filter.setEnabled(True)

    def _on_add_pid_filter(self) -> None:
        self._filtering_model.add(
            self._ui.pid_filter_key.currentIndex(),
            self._ui.pid_filter_key.currentText(),
            self._ui.pid_filter_value.currentText(),
        )
        self._sorting_model.invalidateFilter()
        self._populate_settings_options_filter()

    def _on_pid_filter_menu(self, position: QtCore.QPoint) -> None:
        if not self.sender().selectionModel().selectedRows():
            return
        menu = QtWidgets.QMenu(self)
        remove_action = QtGui.QAction("Remove", self)
        remove_action.triggered.connect(self._on_pid_filter_remove)
        menu.addAction(remove_action)
        menu.exec_(self.sender().mapToGlobal(position))

    def _on_pid_filter_remove(self) -> None:
        selected_row_index = (
            self._ui.pid_filterTable.selectionModel().selectedRows()[0].row()
        )
        self._filtering_model.remove(selected_row_index)
        self._sorting_model.invalidateFilter()
        self._populate_settings_options_filter()
