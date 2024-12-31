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
            item.setData(node, QtCore.Qt.ItemDataRole.UserRole)
            if node == graph.root:
                font = QtGui.QFont()
                font.setBold(True)
                font.setUnderline(True)
                item.setData(font, QtCore.Qt.ItemDataRole.FontRole)
            else:
                if not node.is_runtime:
                    font = QtGui.QFont()
                    font.setItalic(True)
                    item.setData(font, QtCore.Qt.ItemDataRole.FontRole)
            node_info = f"Conan info:\n{node.info}" if node.info else ""
            item.setData(
                f"Package reference: {node.reference}\n"
                f"Package Id: {node.package_id}\n"
                f"Recipe revision: {node.recipe_revision}\n"
                f"{node_info}",
                QtCore.Qt.ItemDataRole.ToolTipRole,
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
                    QtGui.QColor(QtCore.Qt.GlobalColor.red),
                    QtCore.Qt.ItemDataRole.ForegroundRole,
                )
            else:
                if node.is_runtime:
                    item.setData(
                        QtGui.QColor(QtCore.Qt.GlobalColor.black),
                        QtCore.Qt.ItemDataRole.ForegroundRole,
                    )
                else:
                    item.setData(
                        QtGui.QColor(QtCore.Qt.GlobalColor.gray),
                        QtCore.Qt.ItemDataRole.ForegroundRole,
                    )
            parent_item.appendRow(item)
            parent_item = item
