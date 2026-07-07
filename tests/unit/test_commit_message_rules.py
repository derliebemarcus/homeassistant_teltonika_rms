"""Tests for repository commit message validation rules."""

from __future__ import annotations

from unittest.mock import patch

from tools.check_commit_messages import (
    _is_dependabot_identity,
    _is_merge_commit,
    validate_message,
)


def test_validate_message_accepts_repository_formats() -> None:
    assert validate_message("fix: tighten release workflow shell comparison") is None
    assert validate_message("Bump python-socketio from 5.11.2 to 5.16.1") is None
    assert validate_message("Update pytest-cov requirement from <7,>=6 to >=6,<8") is None
    assert validate_message("Merge branch 'main' into codex/qa") is None
    assert (
        validate_message(
            "Release 0.8.3\n\n"
            "fix: ship python-socketio 5.14.0 to remove the current socketio vulnerability\n"
            "fix: document the release workflow correction in release notes\n"
        )
        is None
    )
    assert (
        validate_message(
            "Merge pull request #123 from dependabot/pip/socketio\n\n"
            "this body would normally fail the categorized body-line rule\n"
        )
        is None
    )


def test_validate_message_rejects_invalid_formats() -> None:
    assert validate_message("bump python-socketio from 5.11.2 to 5.16.1") is not None
    assert validate_message("update pytest-cov requirement from <7,>=6 to >=6,<8") is not None
    assert validate_message("merge branch 'main' into codex/qa") is not None
    assert validate_message("Release 0.8.3\nfix: missing blank line") is not None


def test_dependabot_identity_detection_is_narrow() -> None:
    assert _is_dependabot_identity(
        "dependabot[bot]", "49699333+dependabot[bot]@users.noreply.github.com"
    )
    assert _is_dependabot_identity("Some User", "dependabot[bot]@users.noreply.github.com")
    assert not _is_dependabot_identity(
        "github-actions[bot]", "41898282+github-actions[bot]@users.noreply.github.com"
    )
    assert not _is_dependabot_identity("Marcus", "marcus@example.com")


def test_merge_commit_detection_uses_parent_count() -> None:
    with patch(
        "tools.check_commit_messages._git",
        return_value="merge-sha parent-one parent-two\n",
    ):
        assert _is_merge_commit("merge-sha")

    with patch(
        "tools.check_commit_messages._git",
        return_value="commit-sha parent-one\n",
    ):
        assert not _is_merge_commit("commit-sha")
