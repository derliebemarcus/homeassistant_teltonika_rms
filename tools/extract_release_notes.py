#!/usr/bin/env python3
"""Extract release notes for the current manifest version from CHANGELOG.md."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from check_release_notes import extract_section


def main() -> int:
    """Extract the current release section to stdout or a file."""
    manifest_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path("custom_components/teltonika_rms/manifest.json")
    )
    changelog_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("CHANGELOG.md")
    output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    version = str(json.loads(manifest_path.read_text(encoding="utf-8"))["version"]).strip()
    section = extract_section(changelog_path.read_text(encoding="utf-8"), version)
    if not section:
        print(f"Missing or empty changelog section for version {version}", file=sys.stderr)
        return 1

    if output_path is None:
        sys.stdout.write(section)
        if not section.endswith("\n"):
            sys.stdout.write("\n")
    else:
        output_path.write_text(f"{section}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
