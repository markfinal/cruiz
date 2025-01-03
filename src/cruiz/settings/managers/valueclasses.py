#!/usr/bin/env python3

"""Settings context manager value classes."""

import typing
from dataclasses import dataclass


@dataclass
class ScalarValue:
    """Instance representing a scalar value of any type that can be queried via properties of a *Settings class."""  # noqa: E501

    value: typing.Any
    property_name: str
    key: str


@dataclass
class ListValue:
    """
    Instance representing a list of any values that can be queried via properties of a *Settings class.

    The writer mixin assumes the whole list is provided each time it needs to be
    serialised, since there is no other way to determine if an entry needs to be
    removed.
    """  # noqa: E501

    value: typing.List[typing.Any]
    property_name: str
    key: str
    entry_key: str


@dataclass
class DictValue:
    """
    Instance representing a dictionary of any string key and value pairs that can be queried via properties of a *Settings class.

    If any keys have a None value, these are removed from the serialised settings
    by the writer mixin.
    """  # noqa: E501

    value: typing.Any
    property_name: str
    key: str
    entry_key: str
    entry_value: str
