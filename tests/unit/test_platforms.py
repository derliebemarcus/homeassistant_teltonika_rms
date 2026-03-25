"""Tests for platform registration and entity migration expectations."""

from __future__ import annotations

import json
from pathlib import Path

from teltonika_rms.const import UPDATE_PLATFORMS


# Find the true project root by looking for custom_components
def get_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "custom_components" / "teltonika_rms" / "manifest.json").exists():
            return parent
    return current.parents[2]


ROOT = get_root()
MANIFEST = ROOT / "custom_components" / "teltonika_rms" / "manifest.json"
HACS = ROOT / "hacs.json"
ROOT_ICON = ROOT / "custom_components" / "teltonika_rms" / "brand" / "icon.png"
BRAND_ICON = ROOT / "custom_components" / "teltonika_rms" / "brand" / "icon.png"


def test_datetime_platform_removed() -> None:
    assert "datetime" not in UPDATE_PLATFORMS
    assert "button" in UPDATE_PLATFORMS
    assert "switch" in UPDATE_PLATFORMS
    assert "update" in UPDATE_PLATFORMS


def test_manifest_version_present() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert "version" in manifest
    assert manifest["version"]


def test_hacs_root_icon_matches_brand_icon() -> None:
    assert ROOT_ICON.exists()
    assert BRAND_ICON.exists()
    assert ROOT_ICON.read_bytes() == BRAND_ICON.read_bytes()
