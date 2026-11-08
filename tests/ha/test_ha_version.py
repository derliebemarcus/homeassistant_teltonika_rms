"""Enforce the real Home Assistant 2026.11 test baseline."""

from homeassistant.const import __version__ as home_assistant_version


def test_home_assistant_2026_11_baseline() -> None:
    """Reject accidental regressions to an older Home Assistant test runtime."""
    assert home_assistant_version == "2026.11.0", (
        f"Expected Home Assistant 2026.11.x, got {home_assistant_version}"
    )
