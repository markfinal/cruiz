#!/usr/bin/env python3

"""
Child process commands
"""

from __future__ import annotations

import multiprocessing
import re

from cruiz.interop.searchrecipesparameters import SearchRecipesParameters
from cruiz.interop.message import Message, Success

from . import worker


def invoke(
    queue: multiprocessing.Queue[Message], params: SearchRecipesParameters
) -> None:
    """
    Equivalent to:
    'conan search -r <remote_name> [--case-sensitive] <pattern>'

    with optional extra processing when aliases are detected.

    SearchRecipesParameters has dynamic attributes.
    """
    with worker.ConanWorker(queue, params) as api:
        remote_name = params.remote_name  # type: ignore
        alias_aware = params.alias_aware  # type: ignore
        args = {
            "remote_name": remote_name,
            "case_sensitive": params.case_sensitive,  # type: ignore
        }
        try:
            # fill_revisions argument in Conan 1.18.0+
            # cannot use True as the value as it tries to inspect the local cache
            results = api.search_recipes(
                params.pattern,  # type: ignore
                fill_revisions=False,
                **args,
            )
        except TypeError:
            results = api.search_recipes(
                params.pattern,  # type: ignore
                **args,
            )

        if results["results"]:
            results_list = results["results"][0]["items"]
            package_references = [item["recipe"]["id"] for item in results_list]
        else:
            package_references = []
        filtered_results = []
        if alias_aware:
            predicate = re.compile(r'^\s*alias = "(.+)"$', re.MULTILINE)
            for ref in package_references:
                contents, _ = api.get_path(ref, None, None, remote_name)
                alias = None
                matches = predicate.findall(contents)
                if matches:
                    alias = matches[0]
                filtered_results.append((ref, alias))
        else:
            filtered_results = [(ref, None) for ref in package_references]

        queue.put(Success(filtered_results or None))
