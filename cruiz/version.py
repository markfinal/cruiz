#!/usr/bin/env python3

"""
cruiz version specification.

Add .devN to the end of the version number to indicate a development build, N commits
after the last annotated tag.
"""


def get_version() -> str:
    """
    Try to get a fixed version number from the RELEASE_VERSION module (written by
    binary distributions).
    Otherwise, fallback to accessing Git information.
    """
    try:
        from .RELEASE_VERSION import __version__  # type: ignore[import]

        return __version__
    except ImportError:
        import os
        import subprocess
        import sys

        def _describe(cwd: str) -> str:
            if (
                "GITHUB_REF_TYPE" in os.environ
                and os.environ["GITHUB_REF_TYPE"] == "tag"
            ):
                # during GitHub actions, prefer to use the ref pushed
                return os.environ["GITHUB_REF_NAME"]
            else:
                # annotated tags only
                return (
                    subprocess.check_output(["git", "describe", "--tags"], cwd=cwd)
                    .decode("utf-8")
                    .rstrip()
                )

        try:
            root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        except NameError:
            root_dir = os.path.dirname(sys.argv[0])
        try:
            ref_description = _describe(root_dir)
        except subprocess.CalledProcessError:
            return "0.0.0"
        ref_split = ref_description.split("-")
        # drop the v prefix from the tag
        ref_tag = ref_split[0][1:]
        if len(ref_split) == 1:
            __version__ = ref_tag
        else:
            # tag.devN where N is number of commits past the tag
            commit_count = ref_split[1]
            __version__ = f"{ref_tag}.dev{commit_count}"
        return __version__
