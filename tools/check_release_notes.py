#!/usr/bin/env python3
"""Validate changelog release notes for the current manifest version."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def is_version_heading(line: str, version: str) -> bool:
    """Return whether a Markdown heading starts a release for version."""
    escaped = re.escape(version)
    pattern = rf"^##\s+(?:\[{escaped}\](?:\([^)]*\))?|{escaped})(?:\s|$)"
    return re.match(pattern, line) is not None


def extract_section(changelog: str, version: str) -> str:
    """Extract old-style or Release Please notes for version."""
    capture = False
    collected: list[str] = []
    for line in changelog.splitlines():
        if is_version_heading(line, version):
            capture = True
            continue
        if capture and line.startswith("## "):
            break
        if capture:
            collected.append(line)
    return "\n".join(collected).strip()


def main() -> int:
    """Validate that the manifest version has non-empty release notes."""
    manifest_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("custom_components/teltonika_rms/manifest.json")
    )
    changelog_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("CHANGELOG.md")

    version = str(json.loads(manifest_path.read_text(encoding="utf-8"))["version"]).strip()
    section = extract_section(changelog_path.read_text(encoding="utf-8"), version)
    if not section:
        print(f"Missing or empty changelog section for version {version}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
