#!/usr/bin/env python3

"""
cruiz: Conan recipe user interface
"""

import os

from cruiz.resourcegeneration import generate_resources

# resource generation be invoked before resources and MainWindow are imported
generate_resources()


os.environ.setdefault("QT_API", "pyside6")

from cruiz.entrypoint import main  # noqa: E402


if __name__ == "__main__":
    main()
