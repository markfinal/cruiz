#!/usr/bin/env python3

"""
Formatting options to pass to Conan
"""

import typing


def format_options(options: typing.Dict[str, str]) -> typing.List[str]:
    """
    Format the dictionary of options appropriately for Conan 1.x
    """
    options_list = [f"{optkey}={optvalue}" for optkey, optvalue in options.items()]
    return options_list


def format_options_v2(options: typing.Dict[str, str]) -> typing.List[str]:
    """
    Format the dictionary of options appropriately for Conan 2.x
    Expected to be of the form
        -o name/*:option=value
    """
    options_list: typing.List[str] = []
    for optkey, optvalue in options.items():
        assert ":" in optkey
        optkey_split = optkey.split(":")
        options_list.append(f"{optkey_split[0]}/*:{optkey_split[1]}={optvalue}")
    return options_list
