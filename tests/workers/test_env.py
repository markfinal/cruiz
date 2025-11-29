"""Test the worker env functionality."""

import os
import typing

from cruizlib.workers.utils.env import set_env

# pylint: disable=wrong-import-order
import pytest


@pytest.fixture()
def _global_environment() -> typing.Generator[None, None, None]:
    env_copy = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(env_copy)


ENVVAR = "TEST_ENVVAR"


@pytest.mark.parametrize(
    "added,removed,append",
    [
        ({ENVVAR: "True"}, [], False),
        ({ENVVAR: "True"}, [], True),
        ({ENVVAR: None}, [], False),
        ({ENVVAR: 1}, [], False),
        ({ENVVAR: "True"}, [ENVVAR], False),
    ],
)
def test_env_add_and_remove(
    added: typing.Dict[str, typing.Optional[str]],
    removed: typing.List[str],
    append: bool,
    _global_environment: None,
) -> None:
    """Test removing entries from the environment."""
    assert ENVVAR not in os.environ
    if added:
        if append:
            os.environ["TEST_ENVVAR"] = "base"
        set_env(added, [])
        if added[ENVVAR] is not None:
            assert ENVVAR in os.environ
            if append:
                assert "base" in os.environ[ENVVAR]
                assert os.pathsep in os.environ[ENVVAR]
    if removed:
        set_env({}, removed)
        assert ENVVAR not in os.environ
