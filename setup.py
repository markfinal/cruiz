from contextlib import contextmanager
import os
import pathlib
import subprocess
import typing

from setuptools import setup
import setuptools.command.build_py
import setuptools.command.sdist

from src.cruiz.version import get_version


PACKAGE_DIR = pathlib.Path("src", "cruiz")


def _run_command(args: typing.List[str]) -> None:
    print(f"Running {' '.join(args)}", flush=True)
    subprocess.run(args, check=True)


@contextmanager
def _temp_resource_generation(
    callback: typing.Callable[[typing.List[pathlib.Path]], None]
) -> typing.Generator[None, None, None]:
    paths_written: typing.List[pathlib.Path] = []
    callback(paths_written)
    try:
        yield
    finally:
        for path in paths_written:
            path.unlink()


def _compile_qrc(paths_written: typing.List[pathlib.Path]) -> None:
    def _compile_pyside_resources(ver: int) -> pathlib.Path:
        pyside_dir = PACKAGE_DIR / f"pyside{ver}"
        pyside_dir.mkdir(exist_ok=True)
        dst_file = pyside_dir / "resources.py"
        _run_command(
            [
                f"pyside{ver}-rcc",
                "--verbose",
                "-o",
                os.fspath(dst_file),
                os.fspath(PACKAGE_DIR / "resources" / "cruizres.qrc"),
            ]
        )
        return dst_file

    paths_written.append(_compile_pyside_resources(6))


def _compile_uis(paths_written: typing.List[pathlib.Path]) -> None:
    ui_variants = {
        "pyside6": "pyside6-uic",
    }
    for ui_subdir, uic_tool in ui_variants.items():
        ui_dir = PACKAGE_DIR / ui_subdir
        ui_dir.mkdir(exist_ok=True)
        ui_basenames = [
            ui_file.stem
            for ui_file in (PACKAGE_DIR / "resources").iterdir()
            if ui_file.suffix == ".ui"
        ]
        for basename in ui_basenames:
            dst_file = ui_dir / f"{basename}.py"
            _run_command(
                [
                    uic_tool,
                    "-o",
                    os.fspath(dst_file),
                    os.fspath(PACKAGE_DIR / "resources" / f"{basename}.ui"),
                ]
            )
            paths_written.append(dst_file)


def _capture_version(paths_written: typing.List[pathlib.Path]) -> None:
    version_path = PACKAGE_DIR / "RELEASE_VERSION.py"
    with open(version_path, "wt") as version_file:
        version_file.write(f'__version__ = "{get_version()}"')
    paths_written.append(version_path)


class _BuildPyCommand(setuptools.command.build_py.build_py):
    """
    Python build command, run during normal pip install, to generate data from
    resources.
    """

    def run(self) -> None:
        with _temp_resource_generation(_capture_version):
            with _temp_resource_generation(_compile_qrc):
                with _temp_resource_generation(_compile_uis):
                    super().run()


class _SDistCommand(setuptools.command.sdist.sdist):
    """
    Python source distribution command.
    """

    def run(self) -> None:
        with _temp_resource_generation(_capture_version):
            super().run()


setup(
    cmdclass={
        "build_py": _BuildPyCommand,
        "sdist": _SDistCommand,
    },
    version=get_version(),
)
