"""Test globals (could do without these)."""

from cruizlib.globals import get_theme, is_dark_theme, set_theme

# pylint: disable=wrong-import-order
import pytest


def test_theme() -> None:
    """Test global theme."""
    assert get_theme() == "Unknown"
    assert not is_dark_theme()
    with pytest.raises(AssertionError):
        set_theme("DoesNotExist")
    set_theme("Dark")
    assert get_theme() == "Dark"
    assert is_dark_theme()
    set_theme("Light")
    assert get_theme() == "Light"
    assert not is_dark_theme()
