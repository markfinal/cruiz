# cruiz

Written by Mark Final, (c) 2020-2022.

Conan recipe user interface

## Documentation
See the documentation at [Read The Docs](https://cruiz.readthedocs.io/).

## Prerequisites

- Intel x86_64 platforms:
  - Windows 10+
  - Linux (CentOS 7.5+/Ubuntu 18+)
  - macOS (10.13+)
- Apple Silicon platforms:
  - macOS (11.0+)
- Python 3.7-3.10
- Conan 1.17.1+, but not 2.x (these are the versions tested)

All other Python dependencies are installed when the package is installed.

In order to use the dependency graph visualisation, an additional installation of GraphViz is required from https://graphviz.org/download/. Assign the installed location to the preferences.

## Getting started
If you have cloned this repository, you will need:

1. A Python 3 environment. Make a virtual env if necessary. `python3 -m venv <folder to be the env>`
    - Activate the virtual env with either:
        - `source <folder to be the env>/bin/activate` (Linux/macOSX)
        - `<folder to be the env>\Scripts\activate.bat` (Windows cmd)
        - `source <folder to be the env>\Scripts\activate` (Windows bash)

2. Ensure latest pip and wheel are being used. `python -m pip install -U pip wheel`

3. Install cruiz and its dependencies

    - From your local clone:
        - `pip install -r requirements.txt`
        - `pip install --no-build-isolation -e .`

4. Run from any directory

    - From your Python environment shell, `cruiz` or `python -m cruiz`

Step 3 will need to be re-run when the Python dependencies, or the resource files used, change.

## PySide versions
PySide2 and PySide6 have been tested. PySide6 is the default, when running `cruiz`. PySide2 is only available on Intel x86_64 platforms.

On Linux, PySide 6 from PyPI requires modern libstdc++. If you see a launch error indicating `CXXABI_1.3.9` then your distribution is likely too old.

You can alter the default PySide versiont to use, in a number of ways:

1. Use a different entry point

    - `cruiz-pyside2` or `python -m cruiz-pyside2`

2. Use an environment variable

    - `QT_API=pyside2 cruiz`

## Linting
Install linting dependencies with `pip install -r requirements_dev.txt`.

cruiz uses [tox](https://tox.wiki/en/latest/) to automate linting. Use `tox -e lint`.

[flake8](https://flake8.pycqa.org/en/latest/) is used for lint checks, specifically using [black](https://black.readthedocs.io/en/stable/) as the formatter.

[mypy](https://mypy.readthedocs.io/en/stable/) is used for static type checking and validating type annotations.

Python 3.10+ is highly recommended to run the linting steps.

## Making Python packages
`python setup.py sdist` for a source distribution.

`pip wheel --no-deps .` for a wheel.

## Acknowledgements
Many thanks to [Foundry](https://www.foundry.com/) and its developers for support, inspiration, and testing in making cruiz.
