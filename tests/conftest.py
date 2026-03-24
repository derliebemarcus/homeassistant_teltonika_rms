"""Shared pytest configuration for Teltonika RMS tests."""

from __future__ import annotations

import sys
from pathlib import Path

# Find the true project root by looking for custom_components
current = Path(__file__).resolve()
ROOT = current.parents[1]
for parent in current.parents:
    if (parent / "custom_components" / "teltonika_rms" / "manifest.json").exists():
        ROOT = parent
        break

PARENT = ROOT.parent
CUSTOM_COMPONENTS = ROOT / "custom_components"

if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(CUSTOM_COMPONENTS) not in sys.path:
    sys.path.insert(0, str(CUSTOM_COMPONENTS))
