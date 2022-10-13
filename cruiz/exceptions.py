#!/usr/bin/env python3

"""
Exception types
"""


class RecipeInspectionError(Exception):
    """
    An error inspecting the recipe has occurred.
    """


class RecipeDoesNotExistError(Exception):
    """
    Exception class indicating a recipe does not exist.
    """


class RecipeAlreadyOpenError(Exception):
    """
    Exception class indicating a recipe is already open.
    """


class InconsistentSettingsError(Exception):
    """
    An error indicating some settings have been discovered that are inconsistent.
    """
