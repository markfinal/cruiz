#!/usr/bin/env python3

"""Widget for the table of local cache remote."""

import typing
from enum import IntEnum

from PySide6 import QtCore, QtGui, QtWidgets

from cruiz.interop.pod import ConanRemote
from cruiz.widgets.util import BlockSignals


class RemotesTable(QtWidgets.QTableWidget):
    """Table of remotes that can handle moving rows."""

    class _ColumnIndex(IntEnum):
        """Column indices of the remotes table."""

        ENABLED = 0
        NAME = 1
        URL = 2

    remotes_reordered = QtCore.Signal()
    remote_enabled = QtCore.Signal(str, QtCore.Qt.CheckState)

    def __init__(self, parent: typing.Optional[QtWidgets.QWidget] = None) -> None:
        """Initialise a RemotesTable."""
        super().__init__(parent)
        self.itemChanged.connect(self._item_changed)

    def _item_changed(self, item: QtWidgets.QTableWidgetItem) -> None:
        if item.column() == RemotesTable._ColumnIndex.ENABLED:
            name_item = self.item(item.row(), RemotesTable._ColumnIndex.NAME)
            if name_item:
                self.remote_enabled.emit(name_item.text().strip(), item.checkState())

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Override the dropEvent method."""
        if self == event.source():
            index_at_drop = self.indexAt(event.pos())
            source_row = self.selectedItems()[0].row()
            source_items = []
            for col in range(self.columnCount()):
                source_items.append(self.takeItem(source_row, col))
            self.removeRow(source_row)
            self.insertRow(index_at_drop.row())
            for i, item in enumerate(source_items):
                self.setItem(index_at_drop.row(), i, item)
            self.remotes_reordered.emit()
            return
        super().dropEvent(event)

    def add_remote(self, remote: ConanRemote) -> None:
        """Add the specified remote to the table."""
        row_count = self.rowCount()
        enabled_item = QtWidgets.QTableWidgetItem()
        enabled_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsDragEnabled
            | QtCore.Qt.ItemFlag.ItemIsDropEnabled
            | QtCore.Qt.ItemFlag.ItemIsUserCheckable
        )
        enabled_item.setCheckState(
            QtCore.Qt.CheckState.Checked
            if remote.enabled
            else QtCore.Qt.CheckState.Unchecked
        )
        name_item = QtWidgets.QTableWidgetItem(remote.name)
        name_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsDragEnabled
            | QtCore.Qt.ItemFlag.ItemIsDropEnabled
        )
        url_item = QtWidgets.QTableWidgetItem(remote.url)
        url_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsSelectable
            | QtCore.Qt.ItemFlag.ItemIsDragEnabled
            | QtCore.Qt.ItemFlag.ItemIsDropEnabled
        )
        with BlockSignals(self):
            self.setRowCount(row_count + 1)
            self.setItem(row_count, RemotesTable._ColumnIndex.ENABLED, enabled_item)
            self.setItem(row_count, RemotesTable._ColumnIndex.NAME, name_item)
            self.setItem(row_count, RemotesTable._ColumnIndex.URL, url_item)

    def _row_to_remote(self, row_index: int) -> ConanRemote:
        name_item = self.item(row_index, RemotesTable._ColumnIndex.NAME)
        assert name_item is not None
        url_item = self.item(row_index, RemotesTable._ColumnIndex.URL)
        assert url_item is not None
        enabled_item = self.item(row_index, RemotesTable._ColumnIndex.ENABLED)
        assert enabled_item is not None
        remote = ConanRemote(
            name_item.text().strip(),
            url_item.text().strip(),
            enabled_item.checkState() == QtCore.Qt.CheckState.Checked,
        )
        return remote

    def remotes_list(self) -> typing.List[ConanRemote]:
        """Return list of remotes from the table."""
        remotes = []
        for i in range(self.rowCount()):
            remotes.append(self._row_to_remote(i))
        return remotes

    def remove_selected(self) -> ConanRemote:
        """
        Remove the selected row from the table of remotes.

        Note: single selection only, and rows only.
        """
        selected_ranges = self.selectedRanges()
        assert selected_ranges
        row_index = selected_ranges[0].topRow()
        removed_remote = self._row_to_remote(row_index)
        assert row_index == selected_ranges[0].bottomRow()
        self.removeRow(row_index)
        return removed_remote

    def same(self, remotes: typing.List[ConanRemote]) -> bool:
        """
        Are the list of remotes passed in the same as those in the table?.

        There may be more rows in the table than what is in the stored list
        so we only check those from the stored list.
        """
        assert self.rowCount() >= len(remotes)
        for i, remote in enumerate(remotes):
            item = self.item(i, RemotesTable._ColumnIndex.NAME)
            assert item is not None
            table_remote_name = item.text()
            if table_remote_name != remote.name:
                return False
        return True
