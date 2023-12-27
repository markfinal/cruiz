#!/usr/bin/env python3

"""
Qt model for recent Conan configs
"""

import typing

from qtpy import QtCore


class RecentConanConfigModel(QtCore.QAbstractListModel):
    """
    Model representing recent Conan configs
    """

    def __init__(self) -> None:
        super().__init__()
        self._config_paths: typing.Optional[typing.List[str]] = None

    def set_paths(self, paths: typing.List[str]) -> None:
        """
        Set the paths for the Conan configs.
        """
        self.beginResetModel()
        self._config_paths = paths
        self.endResetModel()

    def path(self, index: int) -> str:
        """
        Get a Conan config path specified by its index.
        """
        assert self._config_paths
        return self._config_paths[index]

    def rowCount(self, parent) -> int:  # type: ignore
        if parent.isValid():
            return 0
        if self._config_paths is None:
            return 0
        return len(self._config_paths)

    def headerData(self, section, orientation, role):  # type: ignore
        # pylint: disable=unused-argument
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return "Path"
        return None

    def data(self, index, role):  # type: ignore
        if role == QtCore.Qt.DisplayRole:
            assert self._config_paths
            return self._config_paths[index.row()]
        return None
