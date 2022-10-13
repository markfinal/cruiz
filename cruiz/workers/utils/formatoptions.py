#!/usr/bin/env python3

"""
Formatting options to pass to Conan
"""

import typing


def format_options(options: typing.Dict[str, str]) -> typing.List[str]:
    """
    Format the dictionary of options appropriately for Conan
    """
    options_list = [f"{optkey}={optvalue}" for optkey, optvalue in options.items()]
    return options_list
