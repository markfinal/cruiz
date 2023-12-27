#!/usr/bin/env python3

"""
Utilities for generating SVGs from Conan dependency graphs
"""

import os
import typing

import graphviz
from qtpy import QtCore, QtGui, QtSvg, QtWidgets, QtSvgWidgets

from cruiz.settings.managers.graphvizpreferences import GraphVizSettingsReader
from cruiz.environ import EnvironSaver
from cruiz.interop.packagenode import PackageNode
from cruiz.interop.dependencygraph import DependencyGraph


class DependenciesToDigraph:
    """
    Convert a Conan dependency graph into a GraphViz Digraph
    """

    def __init__(
        self, depgraph: DependencyGraph, rankdir: str, flipped_edges: bool = False
    ) -> None:
        graph = graphviz.Digraph(
            comment="Conan package dependency graph",
            format="svg",
            engine="dot",
        )
        graph.attr(bgcolor="lightsteelblue")
        graph.attr(rankdir=rankdir)
        graph.attr("edge", color="red")
        graph.attr("node", color="blue", style="filled", fillcolor="white")
        self._visited: typing.List[PackageNode] = []
        self._edges: typing.List[typing.Tuple[PackageNode, PackageNode]] = []
        self._visit(graph, depgraph.root, flipped_edges)
        self.digraph = graph

    def _visit(
        self, graph: graphviz.Digraph, node: PackageNode, flipped_edges: bool
    ) -> None:
        def _format_ref(ref: str) -> str:
            return ref.replace("@", "@\n")

        if node not in self._visited:
            node_name_and_id = _format_ref(node.reference)
            if node.is_runtime:
                graph.node(node_name_and_id, id=node_name_and_id)
            else:
                graph.node(node_name_and_id, fillcolor="gray", id=node_name_and_id)
            self._visited.append(node)
        for child in node.children:
            self._visit(graph, child, flipped_edges)
            if (child, node) not in self._edges:
                if flipped_edges:
                    graph.edge(
                        _format_ref(node.reference), _format_ref(child.reference)
                    )
                else:
                    graph.edge(
                        _format_ref(child.reference), _format_ref(node.reference)
                    )
                self._edges.append((child, node))


class DigraphToSVG:
    """
    Convert a Graphviz Digraph to an SVG
    """

    def __init__(self, depstodigraph: DependenciesToDigraph) -> None:
        with EnvironSaver():
            with GraphVizSettingsReader() as settings:
                graphviz_bin_dir = settings.bin_directory.resolve()
            if graphviz_bin_dir:
                os.environ["PATH"] = (
                    QtCore.QDir.toNativeSeparators(graphviz_bin_dir)
                    + os.pathsep
                    + os.environ["PATH"]
                )
            exe_path = QtCore.QStandardPaths.findExecutable("dot")
            if not exe_path:
                # if dot cannot be found, abort before trying any graphviz work
                raise FileNotFoundError(
                    "Cannot find 'dot' to generate dependency graph visualisation"
                )
            self.svg = depstodigraph.digraph.pipe()


class _SVGDialog(QtWidgets.QDialog):
    def __init__(self, renderer: QtSvg.QSvgRenderer) -> None:
        super().__init__()
        self.setWindowTitle("Package dependency graph view")
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self._renderer = renderer
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(renderer)
        self._scene = QtWidgets.QGraphicsScene()
        self._scene.addItem(item)
        self._view = QtWidgets.QGraphicsView(self._scene)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._view)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        self._view.fitInView(self._scene.sceneRect(), QtCore.Qt.KeepAspectRatio)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        self._view.fitInView(self._scene.sceneRect(), QtCore.Qt.KeepAspectRatio)
        super().resizeEvent(event)

    def _context_menu(self, position: QtCore.QPoint) -> None:
        menu = QtWidgets.QMenu(self)
        save_action = QtGui.QAction("Save...", self)
        save_action.triggered.connect(self._on_save)
        menu.addAction(save_action)
        menu.exec_(self.mapToGlobal(position))

    def _on_save(self) -> None:
        new_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save SVG", "", "SVG files (*.svg)"
        )
        if not new_path:
            return
        generator = QtSvg.QSvgGenerator()
        generator.setFileName(new_path)
        generator.setTitle("Conan package dependency graph")
        generator.setDescription("An SVG diagram of the Conan package dependency graph")
        generator.setSize(self._view.sizeHint())
        painter = QtGui.QPainter()
        if painter.begin(generator):
            self._renderer.render(painter)
            painter.end()


class SVGScene(QtWidgets.QGraphicsScene):
    """
    Wrapper around an SVG scene
    """

    def __init__(self, renderer: QtSvg.QSvgRenderer) -> None:
        super().__init__()
        self._renderer = renderer
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(renderer)
        self.addItem(item)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        item = self.itemAt(event.scenePos(), QtGui.QTransform())
        if item and isinstance(item, QtSvgWidgets.QGraphicsSvgItem):
            _SVGDialog(self._renderer).exec_()
            event.setAccepted(True)
        return super().mouseDoubleClickEvent(event)
