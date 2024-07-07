#!/usr/bin/env python3

"""
Conan dependency graph Qt model
"""

from qtpy import QtCore, QtGui

from cruiz.interop.dependencygraph import DependencyGraph


class DependenciesListModel(QtGui.QStandardItemModel):
    """
    Qt model representing the list of dependencies to a recipe
    """

    def __init__(self, graph: DependencyGraph) -> None:
        super().__init__(len(graph.nodes), 1)
        for row, node in enumerate(graph.nodes):
            item = QtGui.QStandardItem()
            item.setText(node.reference)
            item.setData(node, QtCore.Qt.UserRole)
            if node == graph.root:
                font = QtGui.QFont()
                font.setBold(True)
                font.setUnderline(True)
                item.setData(font, QtCore.Qt.FontRole)  # type: ignore
            else:
                if not node.is_runtime:
                    font = QtGui.QFont()
                    font.setItalic(True)
                    item.setData(font, QtCore.Qt.FontRole)  # type: ignore
            node_info = f"Conan info:\n{node.info}" if node.info else ""
            item.setData(
                f"Package reference: {node.reference}\n"
                f"Package Id: {node.package_id}\n"
                f"Recipe revision: {node.recipe_revision}\n"
                f"{node_info}",
                QtCore.Qt.ToolTipRole,  # type: ignore
            )
            self.setItem(row, 0, item)


class DependenciesTreeModel(QtGui.QStandardItemModel):
    """
    Qt model representing the tree of dependencies to a recipe
    """

    def __init__(self, graph: DependencyGraph) -> None:
        super().__init__()
        parent_item = self.invisibleRootItem()
        # TODO: revisit this algorithm
        for node in graph.nodes:
            item = QtGui.QStandardItem()
            item.setText(node.reference)
            if node == graph.root:
                item.setData(
                    QtGui.QColor(QtCore.Qt.red),
                    QtCore.Qt.ForegroundRole,  # type: ignore
                )
            else:
                if node.is_runtime:
                    item.setData(
                        QtGui.QColor(QtCore.Qt.black),
                        QtCore.Qt.ForegroundRole,  # type: ignore
                    )
                else:
                    item.setData(
                        QtGui.QColor(QtCore.Qt.gray),
                        QtCore.Qt.ForegroundRole,  # type: ignore
                    )
            parent_item.appendRow(item)
            parent_item = item
