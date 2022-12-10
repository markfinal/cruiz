#!/usr/bin/env python3

"""
Remote browser page
"""

import typing

from qtpy import QtCore, QtGui

from cruiz.commands.context import ConanConfigBoolean

from cruiz.interop.searchrecipesparameters import SearchRecipesParameters

from cruiz.settings.managers.namedlocalcache import AllNamedLocalCacheSettingsReader

from cruiz.widgets.util import BlockSignals

from .page import Page


class _PackageReferenceModel(QtCore.QAbstractListModel):
    def __init__(self) -> None:
        super().__init__()
        self._list: typing.List[str] = []

    def clear(self) -> None:
        """
        Clear the model
        """
        self.beginResetModel()
        self._list = []
        self.endResetModel()

    def add(self, text: str) -> None:
        """
        Add a package reference to the model
        """
        count = len(self._list)
        self.beginInsertRows(QtCore.QModelIndex(), count, count + 1)
        self._list.append(text)
        self.endInsertRows()

    def rowCount(self, parent) -> int:  # type: ignore
        if parent.isValid():
            return 0
        if not self._list:
            return 0
        return len(self._list)

    def data(self, index, role) -> typing.Any:  # type: ignore
        if role == QtCore.Qt.DisplayRole:
            return self._list[index.row()]
        return None

    def flags(self, index):  # type: ignore
        default_flags = super().flags(index)
        if "->" in self._list[index.row()]:
            return default_flags & ~QtCore.Qt.ItemIsEnabled  # type: ignore[operator]
        return default_flags


class _PackageSearchValidator(QtGui.QValidator):
    """
    Validate the input given to the package search
    """

    def validate(self, input_to_validate: str, pos: int) -> QtGui.QValidator.State:
        # pylint: disable=unused-argument
        if not input_to_validate:
            return QtGui.QValidator.Invalid
        return QtGui.QValidator.Acceptable


class PackageReferencePage(Page):
    """
    Remote browser page for finding package references
    """

    def setup(self, self_ui: typing.Any) -> None:
        """
        Setup the UI for the page
        """
        self._base_setup(self_ui, 0)

        self._revs_enabled = False
        self._model = _PackageReferenceModel()
        self._ui.package_references.setModel(self._model)
        self._ui.package_references.customContextMenuRequested.connect(
            self._on_selected_pkgref_menu
        )

        self._ui.local_cache_name.currentTextChanged.connect(self.on_local_cache_change)
        self._ui.remote.currentTextChanged.connect(self._on_remote_change)

        self._ui.search_pattern.setPlaceholderText("e.g. *xyz*")
        self._ui.search_pattern.setValidator(_PackageSearchValidator(self))
        self._ui.search_pattern.inputRejected.connect(self._pattern_incorrect)
        self._ui.search_pattern.returnPressed.connect(self._search)

        self._ui.package_references.doubleClicked.connect(self._on_pkgref_dclicked)

        self._ui.pkgref_cancel.clicked.connect(self.on_cancel)

        self.refresh_local_cache_names()

    def refresh_local_cache_names(self) -> None:
        """
        Refresh the UI for current local cache names.
        """
        with BlockSignals(self._ui.local_cache_name) as blocked_widget:
            blocked_widget.clear()
            with AllNamedLocalCacheSettingsReader() as cache_names:
                blocked_widget.addItems(cache_names)
            self._ui.local_cache_name.setCurrentIndex(-1)
        self._ui.local_cache_name.setCurrentIndex(0)

    @property
    def package_reference(self) -> str:
        """
        Get the package reference selected on this page
        """
        selection = self._ui.package_references.selectedIndexes()
        assert 1 == len(selection)
        return self._model.data(selection[0], QtCore.Qt.DisplayRole)

    def on_local_cache_change(self, text: str) -> None:
        """
        Called when which local cache has been selected has changed
        """
        self._context.change_cache(text)
        with BlockSignals(self._ui.remote) as blocked_widget:
            blocked_widget.clear()
            for remote in self._context.get_remotes_list():
                blocked_widget.addItem(remote.name)
            blocked_widget.setCurrentIndex(-1)
        self._ui.remote.setCurrentIndex(0)
        self._revs_enabled = self._context.get_boolean_config(
            ConanConfigBoolean.REVISIONS, False
        )
        self._ui.revisions.setChecked(self._revs_enabled)

    def _on_remote_change(self, text: str) -> None:
        # pylint: disable=unused-argument
        self._model.clear()

    def _pattern_incorrect(self) -> None:
        with BlockSignals(self._ui.search_pattern) as blocked_widget:
            blocked_widget.setText("")  # clear doesn't actually clear

    def _enable_progress(self, enable: bool) -> None:
        self._ui.pkgref_ui_group.setEnabled(not enable)
        self._ui.pkgref_progress.setMaximum(0 if enable else 1)
        self._ui.pkgref_cancel.setEnabled(enable)

    def _search(self) -> None:
        self._model.clear()
        self._ui.pkgref_groupbox.setTitle("0 package references found")
        self._enable_progress(True)
        self._ui.pkgref_groupbox.setEnabled(False)
        params = SearchRecipesParameters(
            remote_name=self._ui.remote.currentText(),
            pattern=self._ui.search_pattern.text(),
            case_sensitive=True,
            alias_aware=self._ui.alias_aware.isChecked(),
        )
        self._context.get_package_details(params, self._complete)

    def _complete(self, results: typing.Any, exception: typing.Any) -> None:
        self._enable_progress(False)
        if exception:
            self._ui.pkgref_groupbox.setTitle("Error finding package references")
            self._log_details.stderr(str(exception))
            return
        if results is not None:
            for pkgref, alias in results:
                if alias:
                    self._model.add(f"{pkgref} -> {alias}")
                else:
                    self._model.add(pkgref)
            self._ui.pkgref_groupbox.setTitle(
                f"{len(results)} package references found"
            )
            self._ui.pkgref_groupbox.setEnabled(True)

    def _on_pkgref_dclicked(self, index: QtCore.QModelIndex) -> None:
        # pylint: disable=unused-argument
        if self._revisions_enabled:
            self._open_next_page()
        else:
            # skip recipe revisions
            self.parent().setCurrentIndex(self.page_index + 2)

    def on_cancel(self) -> None:
        """
        Called when the user cancels the operation.
        """
        self._context.cancel()
        self._enable_progress(False)

    def invalidate(self) -> None:
        """
        Invalidate the package reference search.
        """
        self._model.clear()
        self._ui.search_pattern.clear()
