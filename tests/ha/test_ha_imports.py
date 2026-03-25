"""Tests that should only run when Home Assistant dependencies are available."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.ha


@pytest.mark.skipif(
    importlib.util.find_spec("homeassistant") is None,
    reason="homeassistant package is not installed in this environment",
)
def test_integration_module_imports_with_homeassistant() -> None:
    current = Path(__file__).resolve()
    root = current.parents[2]
    for parent in current.parents:
        if (parent / "custom_components" / "teltonika_rms" / "manifest.json").exists():
            root = parent
            break

    integration = root / "custom_components" / "teltonika_rms"
    spec = importlib.util.spec_from_file_location(
        "teltonika_rms",
        integration / "__init__.py",
        submodule_search_locations=[str(integration)],
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
