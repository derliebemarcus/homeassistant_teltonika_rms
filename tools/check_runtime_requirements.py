#!/usr/bin/env python3
"""Verify that Home Assistant runtime requirements match development pins."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MANIFEST = Path("custom_components/teltonika_rms/manifest.json")
DEV_REQUIREMENTS = Path("requirements-dev.txt")
PIN_PATTERN = re.compile(r"^\s*([A-Za-z0-9_.-]+)==([^\s;]+)")


def normalize(name: str) -> str:
    """Return a normalized Python distribution name."""
    return re.sub(r"[-_.]+", "-", name).lower()


def parse_pin(value: str) -> tuple[str, str] | None:
    """Parse a strict name==version requirement."""
    match = PIN_PATTERN.match(value)
    if match is None:
        return None
    return normalize(match.group(1)), match.group(2)


def main() -> int:
    """Compare manifest runtime requirements with requirements-dev.txt."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runtime: dict[str, str] = {}

    for requirement in manifest.get("requirements", []):
        parsed = parse_pin(requirement)
        if parsed is None:
            print(
                f"Runtime requirement must use an exact pin: {requirement}",
                file=sys.stderr,
            )
            return 1
        runtime[parsed[0]] = parsed[1]

    development: dict[str, str] = {}
    for line in DEV_REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        parsed = parse_pin(line)
        if parsed is not None:
            development[parsed[0]] = parsed[1]

    errors: list[str] = []
    for name, version in sorted(runtime.items()):
        development_version = development.get(name)
        if development_version is None:
            errors.append(f"{name}=={version} is missing from {DEV_REQUIREMENTS}")
        elif development_version != version:
            errors.append(
                f"{name} differs: manifest={version}, development={development_version}"
            )

    if errors:
        print("Runtime dependency consistency check failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print(f"Verified {len(runtime)} runtime dependency pin(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
