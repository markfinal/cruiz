#!/usr/bin/env python3

"""
Utility to ensure a default local cache exists
"""

from cruiz.settings.managers.namedlocalcache import (
    AllNamedLocalCacheSettingsReader,
    NamedLocalCacheCreator,
)

from cruiz.constants import DEFAULT_CACHE_NAME


def ensure_default_local_cache() -> None:
    """
    Ensure that the settings has a default local cache
    """
    with AllNamedLocalCacheSettingsReader() as caches:
        need_to_add = DEFAULT_CACHE_NAME not in caches
    if not need_to_add:
        return
    NamedLocalCacheCreator().create(DEFAULT_CACHE_NAME, None, None)
