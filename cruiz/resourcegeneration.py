#!/usr/bin/env python3

"""
Resource generation from PySide
"""

import logging
import os
import pathlib
import platform
import subprocess
import typing

from qtpy import PYSIDE2

if PYSIDE2:
    SUBDIR = "pyside2"
    RCC = "pyside2-rcc"
    UIC = "pyside2-uic"
else:
    SUBDIR = "pyside6"
    RCC = "pyside6-rcc"
    UIC = "pyside6-uic"


logger = logging.getLogger(__name__)


def _run_command_if_out_of_date(
    input: pathlib.Path, output: pathlib.Path, cmd_args: typing.List[str]
) -> bool:
    if output.exists():
        input_mtime = os.path.getmtime(input)
        output_mtime = os.path.getmtime(output)
        if input_mtime < output_mtime:
            return False
    # compile out of date resources
    logger.debug("Running: '%s'", " ".join(cmd_args))
    if platform.system() == "Windows":
        subprocess.check_call(
            cmd_args,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
    else:
        subprocess.check_call(cmd_args)
    return True


def _ensure_resource_file_is_up_to_date(
    dst_dir: pathlib.Path, resources_dir: pathlib.Path
) -> None:
    resource_file = resources_dir / "cruizres.qrc"
    compiled_rcc_file = dst_dir / "resources.py"
    compile_args = [
        RCC,
        "-o",
        str(compiled_rcc_file),
        str(resource_file),
    ]
    _run_command_if_out_of_date(resource_file, compiled_rcc_file, compile_args)


def _ensure_ui_files_are_up_to_date(
    dst_dir: pathlib.Path, resources_dir: pathlib.Path
) -> None:
    for ui_file in resources_dir.glob("*.ui"):
        compiled_ui_file = dst_dir.joinpath(ui_file.name).with_suffix(".py")
        compile_args = [
            UIC,
            "-o",
            str(compiled_ui_file),
            str(ui_file),
        ]
        _run_command_if_out_of_date(ui_file, compiled_ui_file, compile_args)


def generate_resources() -> None:
    """
    Generate PySide resources if out of date
    """
    current_dir = pathlib.Path(__file__).parent
    resources_dir = current_dir / "resources"
    if not resources_dir.exists():
        # resources directory does not exist in binary distributions, so early out
        logger.debug("Resource directory does not exist; compiled resources are fixed")
        return
    logger.debug("Checking for out-of-date resources...")
    _ensure_resource_file_is_up_to_date(current_dir / SUBDIR, resources_dir)
    _ensure_ui_files_are_up_to_date(current_dir / SUBDIR, resources_dir)
