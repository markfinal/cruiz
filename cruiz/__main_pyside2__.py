#!/usr/bin/env python3

"""
cruiz: Conan recipe user interface
"""

import os

os.environ.setdefault("QT_API", "pyside2")

from cruiz.entrypoint import main  # noqa: E402


if __name__ == "__main__":
    main()
