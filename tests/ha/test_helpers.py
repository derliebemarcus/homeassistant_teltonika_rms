"""Tests for shared helper functions."""

from __future__ import annotations

import pytest

from custom_components.teltonika_rms.entity import is_poe_capable_series

pytestmark = pytest.mark.ha


def test_is_poe_capable_series() -> None:
    """Test is_poe_capable_series helper."""
    assert is_poe_capable_series("TSW100") is True
    assert is_poe_capable_series("RUT950") is True
    assert is_poe_capable_series("RUTX11") is False
    assert is_poe_capable_series("OTD140") is True
    assert is_poe_capable_series(None) is False
    assert is_poe_capable_series("") is False
