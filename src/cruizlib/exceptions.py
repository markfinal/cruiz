#!/usr/bin/env python3

"""Exception types."""

import typing


class RecipeInspectionError(Exception):
    """An error inspecting the recipe has occurred."""


class RecipeDoesNotExistError(Exception):
    """Exception class indicating a recipe does not exist."""


class RecipeAlreadyOpenError(Exception):
    """Exception class indicating a recipe is already open."""


class InconsistentSettingsError(Exception):
    """An error indicating some settings have been discovered that are inconsistent."""


class MetaCommandFailureError(Exception):
    """An error coming from a meta command."""

    def __init__(
        self,
        message: str,
        exception_type_name: str,
        exception_traceback: typing.List[str],
    ) -> None:
        """Initialise the exception object."""
        super().__init__(message, exception_type_name, exception_traceback)
        self.exception_type_name = exception_type_name
        self.exception_traceback = exception_traceback
