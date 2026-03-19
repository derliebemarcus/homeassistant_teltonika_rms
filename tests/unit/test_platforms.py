"""Tests for platform registration and entity migration expectations."""

from __future__ import annotations

import json
from pathlib import Path

from teltonika_rms.const import UPDATE_PLATFORMS

ROOT = Path(__file__).resolve().parents[2]
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


def test_manifest_and_hacs_min_homeassistant_version_match() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    hacs = json.loads(HACS.read_text(encoding="utf-8"))
    assert manifest["homeassistant"] == hacs["homeassistant"]


def test_hacs_root_icon_matches_brand_icon() -> None:
    assert ROOT_ICON.exists()
    assert BRAND_ICON.exists()
    assert ROOT_ICON.read_bytes() == BRAND_ICON.read_bytes()
