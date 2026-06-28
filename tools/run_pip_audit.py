"""Run pip-audit with the repository-wide advisory allowlist."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

IGNORE_FILE = Path(__file__).with_name("pip-audit-ignore.txt")


def load_ignored_vulnerabilities() -> list[str]:
    """Load unique advisory identifiers from the shared allowlist."""
    ignored: list[str] = []
    seen: set[str] = set()

    for line_number, raw_line in enumerate(
        IGNORE_FILE.read_text(encoding="utf-8").splitlines(), start=1
    ):
        advisory = raw_line.partition("#")[0].strip()
        if not advisory:
            continue
        if advisory in seen:
            raise ValueError(
                f"Duplicate advisory {advisory!r} in {IGNORE_FILE} at line {line_number}"
            )
        seen.add(advisory)
        ignored.append(advisory)

    return ignored


def build_command(arguments: list[str]) -> list[str]:
    """Build the pip-audit command with all shared exceptions."""
    command = [sys.executable, "-m", "pip_audit", *arguments]
    for advisory in load_ignored_vulnerabilities():
        command.extend(("--ignore-vuln", advisory))
    return command


def main() -> int:
    """Run pip-audit and preserve its exit status."""
    try:
        command = build_command(sys.argv[1:])
    except (OSError, ValueError) as err:
        print(f"Unable to load pip-audit exceptions: {err}", file=sys.stderr)
        return 2

    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
