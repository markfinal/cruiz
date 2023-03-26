#!/usr/bin/env python3

"""
Recipe revisions parameters
"""

import typing

from .commonparameters import CommonParameters


class RecipeRevisionsParameters(CommonParameters):
    """
    Representation of all the arguments to get recipe revisions

    Attributes are dynamically added from the keyword-args passed in.
    """

    def __init__(self, **args: typing.Any) -> None:
        import cruiz.workers.api as workers_api

        super().__init__(workers_api.reciperevisions.invoke)
        for k, v in args.items():
            self.__setattr__(k, v)
