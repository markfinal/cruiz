#!/usr/bin/env python3

"""
Remote browser page
"""

import typing

from qtpy import QtCore, QtGui, QtWidgets

from cruiz.interop.packagerevisionsparameters import PackageRevisionsParameters

from .page import Page


class _PackageRevisionModel(QtCore.QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._prevs: typing.Optional[typing.List[typing.Dict[str, str]]] = None

    def set(self, results: typing.Optional[typing.List[typing.Dict[str, str]]]) -> None:
        """
        Set the results into the model
        """
        self.beginResetModel()
        self._prevs = results
        self.endResetModel()

    def rowCount(self, parent) -> int:  # type: ignore
        if parent.isValid():
            return 0
        if self._prevs is None:
            return 0
        return len(self._prevs)

    def columnCount(self, parent) -> int:  # type: ignore
        # pylint: disable=unused-argument
        if self._prevs is None:
            return 0
        return 2

    def headerData(self, section, orientation, role):  # type: ignore
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            if section == 0:
                return "Revision"
            if section == 1:
                return "Timestamp"
        return None

    def data(self, index, role) -> typing.Any:  # type: ignore
        if role == QtCore.Qt.DisplayRole:
            assert self._prevs
            if index.column() == 0:
                return self._prevs[index.row()]["revision"]
            if index.column() == 1:
                return self._prevs[index.row()]["time"]
        return None


class PackageRevisionPage(Page):
    """
    Remote browser page for displaying package revisions
    """

    def setup(self, self_ui: typing.Any) -> None:
        """
        Setup the UI for the page
        """
        self._base_setup(self_ui, 3)
        self._current_pkgref: typing.Optional[str] = None
        self._model = _PackageRevisionModel()
        self._ui.package_revisions.setModel(self._model)
        self._ui.package_revisions.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeToContents
        )
        self._ui.package_revisions.customContextMenuRequested.connect(
            self._on_selected_pkgref_menu
        )

        self._ui.package_revisions.doubleClicked.connect(self._on_prev_dclicked)
        self._ui.prev_back.clicked.connect(self._on_back)
        self._ui.prev_cancel.clicked.connect(self.on_cancel)
        self._ui.prev_refresh.clicked.connect(self._on_refresh)
        self._ui.prev_restart.clicked.connect(self._on_restart)
        self._ui.prev_pkgref.customContextMenuRequested.connect(self._on_pkgref_menu)

    @property
    def package_reference(self) -> str:
        """
        Get the package reference selected in the current page
        """
        selection = self._ui.package_revisions.selectedIndexes()
        assert len(selection) == 2
        package_rev = self._model.data(selection[0], QtCore.Qt.DisplayRole)
        return f"{self._previous_pkgref}#{package_rev}"

    def _enable_progress(self, enable: bool) -> None:
        self._ui.prev_progress.setMaximum(0 if enable else 1)
        self._ui.prev_buttons.setEnabled(not enable)
        self._ui.prev_cancel.setEnabled(enable)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        # pylint: disable=unused-argument
        self._ui.prev_pkgref.setText(self._previous_pkgref)
        self._compute()

    def _complete(self, results: typing.Any, exception: typing.Any) -> None:
        self._enable_progress(False)
        if exception:
            self._ui.prev_groupbox.setTitle("Error finding package revision")
            self._log_details.stderr(str(exception))
            return
        if results is not None:
            self._model.set(results)
            self._ui.prev_groupbox.setTitle(f"{len(results)} package revisions found")
            self._ui.prev_groupbox.setEnabled(True)
            self._current_pkgref = self._previous_pkgref

    def _on_back(self) -> None:
        self._open_previous_page()

    def _on_prev_dclicked(self, index: QtCore.QModelIndex) -> None:
        # pylint: disable=unused-argument
        self._open_next_page()

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
            self._ui.prev_groupbox.setTitle("0 package revisions found")
            self._model.set(None)
            self._enable_progress(True)
            self._ui.prev_groupbox.setEnabled(False)
            params = PackageRevisionsParameters(
                reference=pkgref,
                remote_name=self._ui.remote.currentText(),
            )
            self._context.get_package_details(params, self._complete)

    def _on_restart(self) -> None:
        self._open_start()

    def _on_copy_pkgref_to_clip(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._ui.prev_pkgref.text())
