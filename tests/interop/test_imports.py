"""Tests for imports that are prohibited."""

import importlib
import sys

MODULES_TO_IMPORT = (
    "cruizlib.constants",
    "cruizlib.interop.commonparameters",
    "cruizlib.interop.message",
    "cruizlib.interop.pod",
)


def test_no_gui_imports() -> None:
    """Ensure no GUI imports are in the cruizlib package."""
    for module_path in MODULES_TO_IMPORT:
        assert importlib.import_module(module_path)
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
