# cruiz

Conan recipe user interface

Written by Mark Final.

![main action workflow](https://github.com/markfinal/cruiz/actions/workflows/main.yml/badge.svg)


## Documentation
See the documentation at [Read The Docs](https://cruiz.readthedocs.io/).

## Prerequisites

- Intel x86_64 platforms:
  - Windows 10+
  - Linux (CentOS 7.5+/Ubuntu 18+)
  - macOS (10.13+)
- Apple Silicon platforms:
  - macOS (11.0+)
- Python 3.7-3.11
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
