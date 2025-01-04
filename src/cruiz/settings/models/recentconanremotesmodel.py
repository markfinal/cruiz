#!/usr/bin/env python3

"""Qt model for recent Conan remotes."""

import typing

from PySide6 import QtCore


class RecentConanRemotesModel(QtCore.QAbstractListModel):
    """Model representing recent Conan remotes."""

    def __init__(self) -> None:
        """Initialise a RecentConanRemotesModel."""
        super().__init__()
        self._urls: typing.Optional[typing.List[str]] = None

    def set_urls(self, urls: typing.List[str]) -> None:
        """Set the URLs for the Conan remotes."""
        self.beginResetModel()
        self._urls = urls
        self.endResetModel()

    def url(self, index: int) -> str:
        """Get a Conan remote identified by its index."""
        assert self._urls
        return self._urls[index]

    def rowCount(self, parent) -> int:  # type: ignore
        """Get the row count of the model."""
        if parent.isValid():
            return 0
        if self._urls is None:
            return 0
        return len(self._urls)

    def headerData(self, section, orientation, role):  # type: ignore
        """Get the header data of the model."""
        # pylint: disable=unused-argument
        if (
            role == QtCore.Qt.ItemDataRole.DisplayRole
            and orientation == QtCore.Qt.Orientation.Horizontal
        ):
            return "URL"
        return None

    def data(self, index, role):  # type: ignore
        """Get data from the model."""
        if role == QtCore.Qt.ItemDataRole.DisplayRole:
            assert self._urls
            return self._urls[index.row()]
        return None
