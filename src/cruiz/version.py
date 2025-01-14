#!/usr/bin/env python3

"""
cruiz version specification.

Add .devN to the end of the version number to indicate a development build, N commits
after the last annotated tag.
"""


def get_version() -> str:
    """
    Try to get a fixed version number from the RELEASE_VERSION module.

    RELEASE_VERSION is written by source and binary distributions.

    Otherwise, fallback to accessing Git information.
    """
    try:
        # in an editable install, RELEASE_VERSION does not exist
        # TODO: the above statement is no longer true
        from .RELEASE_VERSION import __version__

        return __version__
    except ImportError:
        import os
        import pathlib
        import subprocess
        import sys

        def _describe(cwd: pathlib.Path) -> str:
            if (
                "GITHUB_REF_TYPE" in os.environ
                and os.environ["GITHUB_REF_TYPE"] == "tag"
            ):
                # during GitHub actions, prefer to use the ref pushed
                return os.environ["GITHUB_REF_NAME"]
            # annotated tags only
            return subprocess.run(
                ["git", "describe", "--tags"],
                check=True,
                cwd=cwd,
                capture_output=True,
                encoding="utf-8",
                errors="ignore",
            ).stdout.rstrip()

        try:
            file_path = pathlib.Path(__file__)
            root_dir = file_path.parent.parent.absolute()
        except NameError:
            executable_path = pathlib.Path(sys.argv[0])
            root_dir = executable_path.parent
        try:
            ref_description = _describe(root_dir)
        except (FileNotFoundError, subprocess.CalledProcessError):
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
