#!/usr/bin/env python3

"""
Restore settings to defaults
"""

from cruiz.restart import restart_cruiz

from .basesettings import BaseSettings


def factory_reset() -> None:
    """
    Clear all settings, and restart cruiz.
    """
    settings = BaseSettings.make_settings()
    settings.clear()
    restart_cruiz()
