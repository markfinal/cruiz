#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.packagenode import PackageNode
from cruiz.interop.dependencygraph import DependencyGraph

from .utils import worker
from .utils.formatoptions import format_options
from .utils.message import Message, Success


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan lock create'
    """
    with worker.ConanWorker(queue, params) as api:
        # code derived from "conan lock create" command,
        # but aborting before writing a lock file to disk
        from conans.client.profile_loader import profile_from_args
        from conans.model.ref import ConanFileReference
        from conans.model.graph_info import GraphInfo
        from conans.model.env_info import EnvValues
        from conans.client.recorder.action_recorder import ActionRecorder
        from conans.client.graph.graph import (
            RECIPE_CONSUMER,
            RECIPE_VIRTUAL,
        )
        from conans.model.ref import PackageReference

        assert params.profile, "Profile is needed for creating a lock file"

        try:
            phost = profile_from_args(
                [params.profile],
                None,
                format_options(params.options),
                None,
                None,
                params.cwd,
                api.app.cache,
                build_profile=False,
            )
        except TypeError:
            # no conf and build_profile parameters in older Conans
            phost = profile_from_args(
                [params.profile],
                None,
                format_options(params.options),
                None,
                params.cwd,
                api.app.cache,
            )

        phost.process_settings(api.app.cache)

        root_ref = ConanFileReference(
            params.name, params.version, params.user, params.channel, validate=False
        )
        graph_info = GraphInfo(
            profile_host=phost, profile_build=None, root_ref=root_ref
        )

        remotes = api.app.load_remotes()
        recorder = ActionRecorder()

        deps_graph = api.app.graph_manager.load_graph(
            str(params.recipe_path),
            None,
            graph_info,
            None,
            None,
            None,
            remotes,
            recorder,
        )

        # create nodes (derived from conan.graph.printer.print_graph)
        build_time_nodes = deps_graph.build_time_nodes()
        nodes = {}
        for node in sorted(deps_graph.nodes):
            # ensure some attributes, otherwise ConanInfo.dumps() fails
            try:
                if not hasattr(node.conanfile.original_info, "recipe_hash"):
                    node.conanfile.original_info.recipe_hash = None
                if not hasattr(node.conanfile.original_info, "env_values"):
                    node.conanfile.original_info.env_values = EnvValues()
                info = node.conanfile.original_info.dumps()
            except AttributeError:
                # node.conanfile.original_info is only available from Conan 1.47.0+
                info = None

            # layouts folders were introduced in 1.37
            try:
                build_folder = node.conanfile.folders.build
            except AttributeError:
                build_folder = None

            if node.recipe in (RECIPE_CONSUMER, RECIPE_VIRTUAL):
                new_node = PackageNode(
                    node.name,
                    str(node.ref),
                    node.package_id,
                    node.ref.revision,
                    node.conanfile.short_paths,
                    info,
                    True,
                    build_folder,
                )
                nodes[node] = new_node
                continue
            # ignoring the return value from...
            PackageReference(node.ref, node.package_id, node.ref.revision)
            is_runtime = node not in build_time_nodes
            new_node = PackageNode(
                node.name,
                str(node.ref),
                node.package_id,
                node.ref.revision,
                node.conanfile.short_paths,
                info,
                is_runtime,
                build_folder,
            )
            nodes[node] = new_node

        # connect nodes (two-way)
        for node, interop_node in nodes.items():
            for dep in node.dependencies:
                interop_node.children.append(nodes[dep.dst])
                nodes[dep.dst].parents.append(interop_node)

        new_graph = DependencyGraph(list(nodes.values()), new_node)

        queue.put(Success(new_graph))
