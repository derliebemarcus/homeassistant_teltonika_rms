#!/usr/bin/env python3
"""Upload externally generated SARIF results to GitHub Code Scanning."""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_GITHUB_API = "https://api.github.com"
_REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class SarifUploadError(RuntimeError):
    """Raised when GitHub rejects or cannot process a SARIF upload."""


class StalePullRequestBuild(SarifUploadError):
    """Raised when a newer pull-request revision superseded this build."""


def _request_json(
    url: str,
    token: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "homeassistant-teltonika-rms-jenkins",
    }
    if payload is not None:
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=60) as response:  # noqa: S310 - fixed HTTPS API URL
            body = response.read().decode("utf-8")
    except HTTPError as err:
        response_body = err.read().decode("utf-8", errors="replace")
        raise SarifUploadError(
            f"GitHub API request failed with HTTP {err.code}: {response_body}"
        ) from err
    except URLError as err:
        raise SarifUploadError(f"GitHub API request failed: {err.reason}") from err

    if not body:
        return {}
    decoded = json.loads(body)
    if not isinstance(decoded, dict):
        raise SarifUploadError("GitHub API returned an unexpected response shape")
    return decoded


def resolve_analysis_ref(
    *,
    commit_sha: str,
    branch: str,
    pull_request: int | None,
    pull_request_data: dict[str, Any] | None = None,
    skip_stale_pull_request: bool = False,
) -> str:
    """Return the GitHub ref corresponding to the analyzed commit."""
    if pull_request is None:
        normalized_branch = branch.removeprefix("refs/heads/").strip()
        if not normalized_branch:
            raise SarifUploadError("A branch name is required for non-PR builds")
        return f"refs/heads/{normalized_branch}"

    if pull_request_data is None:
        raise SarifUploadError("Pull-request metadata is required for PR builds")

    head = pull_request_data.get("head")
    head_sha = head.get("sha") if isinstance(head, dict) else None
    merge_sha = pull_request_data.get("merge_commit_sha")

    if commit_sha == head_sha:
        return f"refs/pull/{pull_request}/head"
    if merge_sha and commit_sha == merge_sha:
        return f"refs/pull/{pull_request}/merge"

    message = (
        "The analyzed commit does not match the current pull request head or "
        "GitHub merge commit: "
        f"commit={commit_sha}, head={head_sha}, merge={merge_sha}"
    )
    if skip_stale_pull_request:
        raise StalePullRequestBuild(message)
    raise SarifUploadError(message)


def encode_sarif(path: Path) -> str:
    """Return a gzip-compressed, Base64-encoded SARIF document."""
    raw = path.read_bytes()
    if not raw:
        raise SarifUploadError(f"SARIF file is empty: {path}")

    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as err:
        raise SarifUploadError(f"SARIF file is not valid JSON: {path}: {err}") from err

    if not isinstance(decoded, dict) or decoded.get("version") != "2.1.0":
        raise SarifUploadError(f"SARIF file does not declare version 2.1.0: {path}")

    return base64.b64encode(gzip.compress(raw, mtime=0)).decode("ascii")


def upload_sarif(
    *,
    repository: str,
    commit_sha: str,
    ref: str,
    sarif_path: Path,
    tool_name: str | None,
    token: str,
    wait_seconds: int,
) -> None:
    """Upload SARIF and wait for GitHub to finish processing it."""
    payload: dict[str, Any] = {
        "commit_sha": commit_sha,
        "ref": ref,
        "sarif": encode_sarif(sarif_path),
    }
    if tool_name:
        payload["tool_name"] = tool_name

    response = _request_json(
        f"{_GITHUB_API}/repos/{repository}/code-scanning/sarifs",
        token,
        method="POST",
        payload=payload,
    )
    upload_id = response.get("id")
    status_url = response.get("url")
    if not upload_id or not isinstance(status_url, str):
        raise SarifUploadError("GitHub did not return a SARIF upload ID and status URL")

    print(f"SARIF upload accepted: id={upload_id}")
    deadline = time.monotonic() + wait_seconds
    last_status = "pending"

    while time.monotonic() < deadline:
        status = _request_json(status_url, token)
        processing_status = str(status.get("processing_status", "unknown"))
        if processing_status != last_status:
            print(f"SARIF processing status: {processing_status}")
            last_status = processing_status

        if processing_status == "complete":
            return
        if processing_status == "failed":
            errors = status.get("errors")
            raise SarifUploadError(f"GitHub failed to process SARIF: {errors}")
        time.sleep(3)

    raise SarifUploadError(f"Timed out after {wait_seconds} seconds waiting for SARIF processing")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="GitHub owner/repository")
    parser.add_argument("--commit-sha", required=True, help="Analyzed commit SHA")
    parser.add_argument("--branch", required=True, help="Analyzed branch name")
    parser.add_argument("--pull-request", type=int, help="Pull-request number")
    parser.add_argument("--sarif", required=True, type=Path, help="SARIF file")
    parser.add_argument("--tool-name", help="Optional GitHub code-scanning tool name")
    parser.add_argument("--wait-seconds", type=int, default=180)
    parser.add_argument(
        "--fail-on-stale-pr",
        action="store_true",
        help="Fail instead of skipping when a newer PR revision superseded this build",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not _REPOSITORY_PATTERN.fullmatch(args.repository):
        raise SarifUploadError(f"Invalid GitHub repository name: {args.repository}")
    if not args.sarif.is_file():
        raise SarifUploadError(f"SARIF file does not exist: {args.sarif}")

    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise SarifUploadError("GITHUB_TOKEN is not set")

    pull_request_data = None
    if args.pull_request is not None:
        pull_request_data = _request_json(
            f"{_GITHUB_API}/repos/{args.repository}/pulls/{args.pull_request}", token
        )

    try:
        ref = resolve_analysis_ref(
            commit_sha=args.commit_sha,
            branch=args.branch,
            pull_request=args.pull_request,
            pull_request_data=pull_request_data,
            skip_stale_pull_request=not args.fail_on_stale_pr,
        )
    except StalePullRequestBuild as err:
        print(
            f"warning: skipping SARIF upload for a superseded pull-request build: {err}",
            file=sys.stderr,
        )
        return 0

    print(f"Resolved GitHub analysis ref: {ref}")

    upload_sarif(
        repository=args.repository,
        commit_sha=args.commit_sha,
        ref=ref,
        sarif_path=args.sarif,
        tool_name=args.tool_name,
        token=token,
        wait_seconds=args.wait_seconds,
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SarifUploadError as err:
        print(f"error: {err}", file=sys.stderr)
        raise SystemExit(1) from err
