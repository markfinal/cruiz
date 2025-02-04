#!/usr/bin/env python3

"""Conan dependency view."""

from __future__ import annotations

import typing

from PySide6 import QtSvg, QtSvgWidgets, QtWidgets

from cruiz.svggraph import DependenciesToDigraph, DigraphToSVG, SVGScene

if typing.TYPE_CHECKING:
    from cruiz.interop.dependencygraph import DependencyGraph


class DependencyView(QtWidgets.QGraphicsView):
    """View of the dependencies."""

    def clear(self) -> None:
        """Clear the contents of the view."""
        self.setScene(None)

    def visualise(self, depgraph: DependencyGraph, rankdir: int) -> None:
        """Visualise the dependency graph."""
        if not rankdir:
            rank_dir = "LR"
        else:
            assert rankdir == 1
            rank_dir = "TB"
        digraph = DependenciesToDigraph(depgraph, rank_dir)
        svg = DigraphToSVG(digraph)
        self._scene = SVGScene(QtSvg.QSvgRenderer(svg.svg))
        self.setScene(self._scene)


class InverseDependencyViewDialog(QtWidgets.QDialog):
    """View of the inverse of the dependencies."""

    def __init__(
        self,
        depgraph: DependencyGraph,
        parent: typing.Optional[QtWidgets.QWidget] = None,
    ) -> None:
        """Initialise an InverseDependencyViewDialog."""
        super().__init__(parent)
        self.setWindowTitle(f"What uses {depgraph.root.name}")

        # TODO: should this be in cruiz.svggraph to isolate the SVG code?
        digraph = DependenciesToDigraph(depgraph, "LR", flipped_edges=True)
        svg = DigraphToSVG(digraph)
        self._renderer = QtSvg.QSvgRenderer(svg.svg)
        item = QtSvgWidgets.QGraphicsSvgItem()
        item.setSharedRenderer(self._renderer)
        self._scene = QtWidgets.QGraphicsScene()
        self._scene.addItem(item)
        view = QtWidgets.QGraphicsView(self._scene)

        QtWidgets.QVBoxLayout(self).addWidget(view)
