#!/usr/bin/env python3

"""
Create a lockfile but in memory
"""

from __future__ import annotations

import multiprocessing

from cruiz.interop.commandparameters import CommandParameters
from cruiz.interop.packagenode import PackageNode
from cruiz.interop.dependencygraph import DependencyGraph
from cruiz.interop.message import Message, Success

from cruiz.workers.utils.formatoptions import format_options_v2

from . import worker


def invoke(queue: multiprocessing.Queue[Message], params: CommandParameters) -> None:
    """
    Run 'conan lock create'
    """
    with worker.ConanWorker(queue, params) as api:
        try:
            import dataclasses
            import os

            from conans.client.graph.graph import (
                RECIPE_CONSUMER,
                RECIPE_VIRTUAL,
            )

            remotes = api.remotes.list()

            # fake command line arguments
            @dataclasses.dataclass
            class FakeCLIArguments:
                name = params.name
                version = params.version
                user = params.user
                channel = params.channel
                build: None = None
                update = True
                build_require: None = None
                profile_build: None = None
                profile_host: None = None
                settings_build: None = None
                options_build = format_options_v2(params.options)
                conf_build: None = None
                settings_host: None = None
                options_host = format_options_v2(params.options)
                conf_host: None = None

            args = FakeCLIArguments()

            profile_host, profile_build = api.profiles.get_profiles_from_args(args)

            lockfile = None
            # first get enough information about recipes
            assert params.recipe_path
            deps_graph = api.graph.load_graph_consumer(
                os.fspath(params.recipe_path),
                args.name,
                args.version,
                args.user,
                args.channel,
                profile_host,
                profile_build,
                lockfile,
                remotes,
                args.build,
                args.update,
                is_build_require=args.build_require,
            )

            # then get binary information, e.g. package_ids
            api.graph.analyze_binaries(
                deps_graph,
                args.build,
                remotes=remotes,
                update=args.update,
                lockfile=lockfile,
            )

            # create nodes (derived from conan.graph.printer.print_graph)
            # continuing to use this in Conan 2
            build_time_nodes = deps_graph.build_time_nodes()
            nodes = {}
            for node in sorted(deps_graph.nodes):
                info = node.conanfile.original_info.dumps()
                build_folder = node.conanfile.folders.build
                # in Conan 2, there are no short paths
                short_paths = False

                if node.conanfile.info.invalid:
                    raise ValueError(node.conanfile.info.invalid)

                if node.recipe in (RECIPE_CONSUMER, RECIPE_VIRTUAL):
                    new_node = PackageNode(
                        node.name,
                        str(node.ref),
                        node.package_id,
                        node.ref.revision,
                        short_paths,
                        info,
                        True,
                        build_folder,
                    )
                    root_node = nodes[node] = new_node
                    continue
                is_runtime = node not in build_time_nodes
                new_node = PackageNode(
                    node.name,
                    str(node.ref),
                    node.package_id,
                    node.ref.revision,
                    short_paths,
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

            new_graph = DependencyGraph(list(nodes.values()), root_node)

            queue.put(Success(new_graph))
        except Exception as exc:
            print(exc)
            raise
