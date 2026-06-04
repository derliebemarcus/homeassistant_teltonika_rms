#!/usr/bin/env python3
"""Print a compact pytest result summary from JUnit XML."""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _status(case: ET.Element) -> str:
    if case.find("failure") is not None:
        return "FAILED"
    if case.find("error") is not None:
        return "ERROR"
    if case.find("skipped") is not None:
        return "SKIPPED"
    return "PASSED"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: print_pytest_summary.py <junit-xml-path>")
        return 2

    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print("[summary] No JUnit XML report found. Pytest likely failed before reporting.")
        return 0

    try:
        tree = ET.parse(report_path)
    except ET.ParseError:
        print(
            "[summary] Invalid or empty JUnit XML report. "
            "Pytest likely failed before writing results."
        )
        return 0
    root = tree.getroot()
    test_cases = list(root.iter("testcase"))

    if not test_cases:
        print("[summary] No test cases found in report.")
        return 0

    name_width = max(
        len(f"{case.attrib.get('classname', '')}::{case.attrib.get('name', '')}".strip(":"))
        for case in test_cases
    )
    name_width = max(name_width, len("Test"))
    duration_width = len("Duration(s)")

    print("")
    print("Test Summary")
    print(f"{'Test'.ljust(name_width)}  {'Duration(s)'.rjust(duration_width)}  Result")
    print(f"{'-' * name_width}  {'-' * duration_width}  ------")

    counts = {"PASSED": 0, "FAILED": 0, "ERROR": 0, "SKIPPED": 0}
    total_duration = 0.0

    for case in test_cases:
        name = f"{case.attrib.get('classname', '')}::{case.attrib.get('name', '')}".strip(":")
        duration = float(case.attrib.get("time", "0") or "0")
        result = _status(case)
        counts[result] += 1
        total_duration += duration
        print(f"{name.ljust(name_width)}  {duration:>{duration_width}.3f}  {result}")

    print("")
    print(
        "Totals: "
        f"passed={counts['PASSED']}, failed={counts['FAILED']}, "
        f"errors={counts['ERROR']}, skipped={counts['SKIPPED']}, "
        f"duration={total_duration:.3f}s"
    )
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
