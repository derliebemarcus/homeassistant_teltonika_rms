from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import pytest

from tools.upload_github_sarif import (
    SarifUploadError,
    StalePullRequestBuild,
    encode_sarif,
    resolve_analysis_ref,
)


def test_resolve_branch_ref() -> None:
    assert (
        resolve_analysis_ref(
            commit_sha="a" * 40,
            branch="feature/example",
            pull_request=None,
        )
        == "refs/heads/feature/example"
    )


def test_resolve_pull_request_head_ref() -> None:
    commit_sha = "a" * 40
    assert (
        resolve_analysis_ref(
            commit_sha=commit_sha,
            branch="feature/example",
            pull_request=112,
            pull_request_data={
                "head": {"sha": commit_sha},
                "merge_commit_sha": "b" * 40,
            },
        )
        == "refs/pull/112/head"
    )


def test_resolve_pull_request_merge_ref() -> None:
    commit_sha = "b" * 40
    assert (
        resolve_analysis_ref(
            commit_sha=commit_sha,
            branch="feature/example",
            pull_request=112,
            pull_request_data={
                "head": {"sha": "a" * 40},
                "merge_commit_sha": commit_sha,
            },
        )
        == "refs/pull/112/merge"
    )


def test_reject_unrelated_pull_request_commit() -> None:
    with pytest.raises(SarifUploadError, match="does not match"):
        resolve_analysis_ref(
            commit_sha="c" * 40,
            branch="feature/example",
            pull_request=112,
            pull_request_data={
                "head": {"sha": "a" * 40},
                "merge_commit_sha": "b" * 40,
            },
        )


def test_mark_superseded_pull_request_build_as_stale() -> None:
    with pytest.raises(StalePullRequestBuild, match="does not match"):
        resolve_analysis_ref(
            commit_sha="c" * 40,
            branch="feature/example",
            pull_request=112,
            pull_request_data={
                "head": {"sha": "a" * 40},
                "merge_commit_sha": "b" * 40,
            },
            skip_stale_pull_request=True,
        )


def test_encode_sarif_round_trip(tmp_path: Path) -> None:
    document = {"version": "2.1.0", "runs": []}
    sarif_path = tmp_path / "result.sarif"
    sarif_path.write_text(json.dumps(document), encoding="utf-8")

    encoded = encode_sarif(sarif_path)
    decoded = gzip.decompress(base64.b64decode(encoded)).decode("utf-8")

    assert json.loads(decoded) == document


def test_reject_non_sarif_json(tmp_path: Path) -> None:
    sarif_path = tmp_path / "result.sarif"
    sarif_path.write_text('{"version": "1.0"}', encoding="utf-8")

    with pytest.raises(SarifUploadError, match="version 2.1.0"):
        encode_sarif(sarif_path)
