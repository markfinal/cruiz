#!/usr/bin/env python3

"""Remote browser page."""

from __future__ import annotations

import typing

from PySide6 import QtCore, QtGui, QtWidgets

from cruiz.interop.reciperevisionsparameters import RecipeRevisionsParameters

from .page import Page

if typing.TYPE_CHECKING:
    from cruiz.pyside6.remote_browser import Ui_remotebrowser


class _RecipeRevisionModel(QtCore.QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._rrevs: typing.Optional[typing.List[typing.Dict[str, str]]] = None

    def set(self, results: typing.Optional[typing.List[typing.Dict[str, str]]]) -> None:
        """Set the results against the model."""
        self.beginResetModel()
        self._rrevs = results
        self.endResetModel()

    def rowCount(self, parent) -> int:  # type: ignore
        """Get the number of rows in the model."""
        if parent.isValid():
            return 0
        if self._rrevs is None:
            return 0
        return len(self._rrevs)

    def columnCount(self, parent) -> int:  # type: ignore
        """Get the number of columns in the model."""
        # pylint: disable=unused-argument
        if self._rrevs is None:
            return 0
        return 2

    def headerData(self, section, orientation, role):  # type: ignore
        """Get headers from the model."""
        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
        ):
            if not section:
                return "Revision"
            if section == 1:
                return "Timestamp"
        return None

    def data(self, index, role) -> typing.Any:  # type: ignore
        """Get data from the model."""
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            assert self._rrevs
            if not index.column():
                return self._rrevs[index.row()]["revision"]
            if index.column() == 1:
                return self._rrevs[index.row()]["time"]
        return None


class RecipeRevisionPage(Page):
    """Remote browser page for recipe revisions."""

    def setup(self, self_ui: Ui_remotebrowser) -> None:
        """Set up the UI for the page."""
        self._base_setup(self_ui, 1)
        self._current_pkgref: typing.Optional[str] = None
        self._model = _RecipeRevisionModel()
        self._ui.recipe_revisions.setModel(self._model)
        self._ui.recipe_revisions.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.ResizeToContents
        )
        self._ui.recipe_revisions.customContextMenuRequested.connect(
            self._on_selected_pkgref_menu
        )

        self._ui.recipe_revisions.doubleClicked.connect(self._on_rrev_dclicked)
        self._ui.rrev_back.clicked.connect(self._on_back)
        self._ui.rrev_cancel.clicked.connect(self.on_cancel)
        self._ui.rrev_refresh.clicked.connect(self._on_refresh)
        self._ui.rrev_pkgref.customContextMenuRequested.connect(self._on_pkgref_menu)

    @property
    def package_reference(self) -> str:
        """Get the package reference for the selection on this page."""
        selection = self._ui.recipe_revisions.selectedIndexes()
        assert len(selection) == 2  # num columns in row
        rrev = self._model.data(selection[0], QtCore.Qt.ItemDataRole.DisplayRole)
        return f"{self._previous_pkgref}#{rrev}"

    def _on_copy_pkgref_to_clip(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._ui.rrev_pkgref.text())

    def _enable_progress(self, enable: bool) -> None:
        self._ui.rrev_progress.setMaximum(0 if enable else 1)
        self._ui.rrev_buttons.setEnabled(not enable)
        self._ui.rrev_cancel.setEnabled(enable)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Override the widget's showEvent method."""
        # pylint: disable=unused-argument
        self._ui.rrev_pkgref.setText(self._previous_pkgref)
        self._compute()

    def _complete(self, results: typing.Any, exception: typing.Any) -> None:
        self._enable_progress(False)
        if exception:
            self._ui.rrev_groupbox.setTitle("Error finding recipe revision")
            self._log_details.stderr(str(exception))
            return
        if results is not None:
            self._model.set(results)
            self._ui.rrev_groupbox.setTitle(f"{len(results)} recipe revisions found")
            self._ui.rrev_groupbox.setEnabled(True)
            self._current_pkgref = self._previous_pkgref

    def _on_back(self) -> None:
        self._ui.stackedWidget.setCurrentWidget(self._ui.pkgref)

    def _on_rrev_dclicked(self, index: QtCore.QModelIndex) -> None:
        # pylint: disable=unused-argument
        self._ui.stackedWidget.setCurrentWidget(self._ui.package_id)

    def on_cancel(self) -> None:
        """Call when the user cancels the operation."""
        self._context.cancel()
        self._enable_progress(False)

    def _on_refresh(self) -> None:
        self._current_pkgref = None
        self._compute()

    def _compute(self) -> None:
        pkgref = self._previous_pkgref
        if self._current_pkgref != pkgref:
            self._ui.pkgref_groupbox.setTitle("0 recipe revisions found")
            self._model.set(None)
            self._enable_progress(True)
            self._ui.rrev_groupbox.setEnabled(False)
            params = RecipeRevisionsParameters(
                reference=pkgref,
                remote_name=self._ui.remote.currentText(),
            )
            self._context.get_package_details(params, self._complete)
