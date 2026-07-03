#!/usr/bin/env python3
"""Print unresolved Trivy findings from a JSON report."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _text(value: Any, default: str = "-") -> str:
    if value is None or value == "":
        return default
    return str(value)


def _print_vulnerabilities(result: dict[str, Any]) -> int:
    target = _text(result.get("Target"), "unknown target")
    findings = result.get("Vulnerabilities") or []
    for finding in findings:
        severity = _text(finding.get("Severity"))
        identifier = _text(finding.get("VulnerabilityID"))
        package = _text(finding.get("PkgName"))
        installed = _text(finding.get("InstalledVersion"))
        fixed = _text(finding.get("FixedVersion"))
        print(
            f"{severity} {identifier}: {package} {installed} "
            f"(fixed: {fixed}; target: {target})"
        )
    return len(findings)


def _print_generic(result: dict[str, Any], key: str, kind: str) -> int:
    target = _text(result.get("Target"), "unknown target")
    findings = result.get(key) or []
    for finding in findings:
        severity = _text(finding.get("Severity"))
        identifier = _text(finding.get("ID") or finding.get("RuleID"))
        title = _text(finding.get("Title"))
        print(f"{severity} {kind} {identifier}: {title} (target: {target})")
    return len(findings)


def main() -> int:
    report = Path(sys.argv[1] if len(sys.argv) > 1 else "trivy-report.json")
    data = json.loads(report.read_text(encoding="utf-8"))
    total = 0
    for result in data.get("Results") or []:
        total += _print_vulnerabilities(result)
        total += _print_generic(result, "Misconfigurations", "misconfiguration")
        total += _print_generic(result, "Secrets", "secret")
    print(f"Unresolved Trivy findings: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
