#!/usr/bin/env python3

"""Widget for a table of key-value pairs."""

from enum import IntEnum

from cruiz.widgets.util import BlockSignals

from qtpy import QtCore, QtWidgets


class KeyValueTable(QtWidgets.QTableWidget):
    """Table of key-value pairs."""

    class ColumnIndex(IntEnum):
        """Column indices of the table."""

        KEY = 0
        VALUE = 1

    def add_key_value_pair(self, key: str, value: str) -> None:
        """Add a key-value pair to the table."""
        row_count = self.rowCount()
        key_item = QtWidgets.QTableWidgetItem(key)
        key_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        value_item = QtWidgets.QTableWidgetItem(value)
        value_item.setFlags(
            QtCore.Qt.ItemFlag.ItemIsEnabled
            | QtCore.Qt.ItemFlag.ItemIsEditable
            | QtCore.Qt.ItemFlag.ItemIsSelectable
        )
        with BlockSignals(self) as blocked_widget:
            assert isinstance(blocked_widget, KeyValueTable)
            blocked_widget.setRowCount(row_count + 1)
            with BlockSignals(blocked_widget.model()):
                blocked_widget.setItem(
                    row_count, KeyValueTable.ColumnIndex.KEY, key_item
                )
                blocked_widget.setItem(
                    row_count, KeyValueTable.ColumnIndex.VALUE, value_item
                )

    def remove_selected(self) -> str:
        """
        Remove the selected row.

        Selections are single-row selection.

        Remove that selected row, and return the key string for that removed row.
        """
        selected_ranges = self.selectedRanges()
        assert selected_ranges
        row_index = selected_ranges[0].topRow()
        assert row_index == selected_ranges[0].bottomRow()
        item = self.item(row_index, KeyValueTable.ColumnIndex.KEY)
        assert item is not None
        selected_key = item.text()
        self.removeRow(row_index)
        return selected_key
