#!/usr/bin/env python3
"""Validate commit messages against the repository format rules."""

from __future__ import annotations

import re
import subprocess
import sys

CATEGORY_RE = re.compile(r"^(add|change|deprecate|remove|fix|build|chore)(\(.*\))?: [^ ].*")
BYPASS_PREFIX_RE = re.compile(r"^(Update|Bump|Merge|Revert)\b")
DEPENDABOT_NAME = "dependabot[bot]"


def _git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True)


def _meaningful_lines(message: str) -> list[str]:
    return [line for line in message.splitlines() if line and not line.startswith("#")]


def validate_message(message: str) -> str | None:
    lines = [line for line in message.splitlines() if not line.startswith("#")]
    meaningful = _meaningful_lines(message)
    if not meaningful:
        return "commit message must not be empty"
    if BYPASS_PREFIX_RE.match(meaningful[0]):
        return None

    if len(meaningful) == 1:
        if not CATEGORY_RE.match(meaningful[0]):
            return "single-line commits must start with a category (e.g. add:, change:, fix:)"
        return None

    summary = None
    body_started = False
    saw_blank_after_summary = False
    categorized_body_lines = 0

    for line in lines:
        if summary is None:
            if not line.strip():
                continue
            summary = line
            continue
        if not body_started:
            if not line.strip():
                saw_blank_after_summary = True
                continue
            if not saw_blank_after_summary:
                return "multi-line commit messages require a summary line followed by a blank line"
            body_started = True
        if not line.strip():
            continue
        if CATEGORY_RE.match(line):
            categorized_body_lines += 1

    if summary is None:
        return "commit message must not be empty"

    if not CATEGORY_RE.match(summary) and categorized_body_lines == 0:
        return (
            "multi-line commits require a categorized summary or at least one categorized body line"
        )
    return None


def _is_dependabot_identity(name: str, email: str) -> bool:
    normalized_name = name.strip().lower()
    normalized_email = email.strip().lower()
    return normalized_name == DEPENDABOT_NAME or DEPENDABOT_NAME in normalized_email


def _is_dependabot_commit(sha: str) -> bool:
    author = _git("log", "-1", "--format=%an%n%ae%n%cn%n%ce", sha).splitlines()
    if len(author) != 4:
        return False
    author_name, author_email, committer_name, committer_email = author
    return _is_dependabot_identity(author_name, author_email) or _is_dependabot_identity(
        committer_name, committer_email
    )


def main() -> int:
    commit_range = sys.argv[1] if len(sys.argv) > 1 else "HEAD^..HEAD"
    shas = [sha for sha in _git("rev-list", "--reverse", commit_range).splitlines() if sha]
    if not shas:
        print(f"No commits found in range {commit_range}")
        return 0

    failed = False
    for sha in shas:
        if _is_dependabot_commit(sha):
            continue
        message = _git("log", "-1", "--format=%B", sha)
        error = validate_message(message)
        if error:
            failed = True
            print(f"{sha[:7]}: {error}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
