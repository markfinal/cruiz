from contextlib import contextmanager
import os
import subprocess
import typing

from setuptools import setup, find_packages
import setuptools.command.build_py
import setuptools.command.sdist

from cruiz.version import get_version


def _run_command(args: typing.List[str]) -> None:
    print(f"Running {' '.join(args)}", flush=True)
    subprocess.check_call(args)


@contextmanager
def _temp_resource_generation(
    callback: typing.Callable[[typing.List[str]], None]
) -> typing.Generator[None, None, None]:
    paths_written: typing.List[str] = []
    callback(paths_written)
    try:
        yield
    finally:
        for path in paths_written:
            os.unlink(path)


def _compile_qrc(paths_written: typing.List[str]) -> None:
    def _compile_pyside_resources(ver: int) -> str:
        if not os.path.isdir(f"cruiz/pyside{ver}"):
            os.makedirs(f"cruiz/pyside{ver}")
        dst_file = f"cruiz/pyside{ver}/resources.py"
        _run_command(
            [
                f"pyside{ver}-rcc",
                "--verbose",
                "-o",
                dst_file,
                "cruiz/resources/cruizres.qrc",
            ]
        )
        return dst_file

    paths_written.append(_compile_pyside_resources(6))
    paths_written.append(_compile_pyside_resources(2))


def _compile_uis(paths_written: typing.List[str]) -> None:
    ui_variants = {
        "pyside6": "pyside6-uic",
        "pyside2": "pyside2-uic",
    }
    for ui_subdir, uic_tool in ui_variants.items():
        ui_dir = f"cruiz/{ui_subdir}"
        if not os.path.isdir(ui_dir):
            os.makedirs(ui_dir)
        ui_basenames = [
            os.path.splitext(ui_file)[0]
            for ui_file in os.listdir("cruiz/resources")
            if os.path.splitext(ui_file)[1] == ".ui"
        ]
        for basename in ui_basenames:
            dst_file = f"{ui_dir}/{basename}.py"
            _run_command(
                [
                    uic_tool,
                    "-o",
                    dst_file,
                    f"cruiz/resources/{basename}.ui",
                ]
            )
            paths_written.append(dst_file)


def _capture_version(paths_written: typing.List[str]) -> None:
    version_path = "cruiz/RELEASE_VERSION.py"
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


requirements_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "requirements.txt"
)


with open(requirements_path) as requirements_file:
    requires = requirements_file.readlines()


readme_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "README.md"
)


with open(readme_path) as readme_file:
    readme = readme_file.read()


setup(
    cmdclass={
        "build_py": _BuildPyCommand,
        "sdist": _SDistCommand,
    },
    name="cruiz",
    version=get_version(),
    description="Conan recipe user interface",
    long_description=readme,
    long_description_content_type='text/markdown',
    author="Mark Final",
    author_email="markfinal@hotmail.com",
    url="https://github.com/markfinal/cruiz",
    packages=find_packages(),
    install_requires=requires,
    entry_points={
        "gui_scripts": [
            "cruiz = cruiz.__main__:main",
            "cruiz-pyside2 = cruiz.__main_pyside2__:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7, <3.11",
    project_urls={
        'Documentation': 'https://cruiz.readthedocs.io/en/latest/',
        'GitHub': 'https://github.com/markfinal/cruiz',
    },
)
