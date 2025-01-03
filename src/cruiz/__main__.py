#!/usr/bin/env python3

"""
cruiz: Conan recipe user interface
"""

import os

from cruiz.entrypoint import main
from cruiz.resourcegeneration import generate_resources

# resource generation be invoked before resources and MainWindow are imported
generate_resources()


os.environ.setdefault("QT_API", "pyside6")


if __name__ == "__main__":
    main()
