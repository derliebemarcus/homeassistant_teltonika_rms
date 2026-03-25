"""Tests for translation consistency."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


# Find the true project root by looking for custom_components
def get_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "custom_components" / "teltonika_rms" / "manifest.json").exists():
            return parent
    return current.parents[2]


ROOT = get_root()
INTEGRATION_DIR = ROOT / "custom_components" / "teltonika_rms"
STRINGS = INTEGRATION_DIR / "strings.json"
TRANSLATIONS_DIR = INTEGRATION_DIR / "translations"

PLACEHOLDER_PATTERNS = (
    re.compile(r"__[^_]+__"),
    re.compile(r"\[\[\d+\]\]"),
    re.compile(r"\[\[[^\]]*$"),
)


def _flatten(node: Any, prefix: str = "") -> dict[str, str]:
    output: dict[str, str] = {}
    if isinstance(node, dict):
        for key, value in node.items():
            child_prefix = f"{prefix}.{key}" if prefix else key
            output.update(_flatten(value, child_prefix))
    elif isinstance(node, str):
        output[prefix] = node
    return output


def test_translation_keys_match_reference() -> None:
    reference = json.loads(STRINGS.read_text(encoding="utf-8"))
    reference_keys = set(_flatten(reference))

    for file_path in sorted(TRANSLATIONS_DIR.glob("*.json")):
        data = json.loads(file_path.read_text(encoding="utf-8"))
        keys = set(_flatten(data))
        assert keys == reference_keys, f"{file_path.name} key mismatch"


def test_translation_text_has_no_unresolved_placeholders() -> None:
    for file_path in sorted(TRANSLATIONS_DIR.glob("*.json")):
        data = json.loads(file_path.read_text(encoding="utf-8"))
        flat = _flatten(data)
        for key, text in flat.items():
            assert isinstance(text, str)
            for pattern in PLACEHOLDER_PATTERNS:
                assert not pattern.search(text), (
                    f"{file_path.name}:{key} contains placeholder artifact"
                )
