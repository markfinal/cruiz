"""Tests for imports that are prohibited."""

import importlib
import os
import pathlib
import sys


def test_no_gui_imports() -> None:
    """Ensure no GUI imports are in the cruizlib package."""
    current_file_path = pathlib.Path(__file__)
    tests_dir = current_file_path.parent
    root_dir = tests_dir.parent
    src_dir = root_dir / "src"
    cruiz_lib_src = src_dir / "cruizlib"
    for file in cruiz_lib_src.rglob("*.py"):
        if "v1" in os.fspath(file) or "v2" in os.fspath(file):
            # those modules that import conan cannot be tested "in process"
            continue
        module_path = os.fspath(file.relative_to(src_dir)).replace(os.path.sep, ".")
        module_name = module_path.replace(".py", "")
        assert importlib.import_module(module_name)
    modules = list(sys.modules.keys())
    modules = [module for module in modules if module.startswith("PySide")]
    allow_list_prefix = ("PySide6.support",)
    modules = [module for module in modules if not module.startswith(allow_list_prefix)]
    allow_list_exact = (
        "PySide6",
        "PySide6.QtCore",
    )
    modules = [module for module in modules if module not in allow_list_exact]
    assert not modules
