"""Regression: Opire workspace identity + fork/push SSOT = task.repository."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from swarm.farm_execution_engine import (
    clone_repository,
    github_slug_from_remote_url,
    normalize_repo_slug,
    resolve_git_binary,
    workspace_matches_repository,
)
from swarm.farm_github_live import ensure_user_fork, live_submit_draft_pr, push_branch
from swarm.farm_stabilization import quarantine_workspace_safe


def _git_init(repo: Path, *, remote: str | None = None) -> None:
    git = resolve_git_binary()
    assert git
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run([git, "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [git, "config", "user.email", "farm@test.local"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [git, "config", "user.name", "Farm Test"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "README.md").write_text("# fixture\n", encoding="utf-8")
    subprocess.run([git, "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [git, "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    if remote:
        subprocess.run(
            [git, "remote", "add", "origin", remote],
            cwd=repo,
            check=True,
            capture_output=True,
        )


def test_normalize_and_slug_helpers() -> None:
    assert normalize_repo_slug("radumarias/rencfs") == "radumarias/rencfs"
    assert (
        normalize_repo_slug("https://github.com/radumarias/rencfs.git")
        == "radumarias/rencfs"
    )
    assert (
        github_slug_from_remote_url("git@github.com:uytyutu/Genesis-AI-Engine.git")
        == "uytyutu/genesis-ai-engine"
    )


def test_unrelated_workspace_mismatch(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    src = tmp_path / "src"
    _git_init(
        src,
        remote="https://github.com/uytyutu/Genesis-AI-Engine.git",
    )
    out = workspace_matches_repository(src, "radumarias/rencfs")
    assert out["ok"] is False
    assert out["error"] == "WORKSPACE_REPOSITORY_MISMATCH"
    assert out["actual"] == "uytyutu/genesis-ai-engine"
    assert out["expected"] == "radumarias/rencfs"


def test_matching_workspace_allows_reuse(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    src = tmp_path / "src"
    _git_init(src, remote="https://github.com/radumarias/rencfs.git")
    out = workspace_matches_repository(src, "radumarias/rencfs")
    assert out["ok"] is True
    assert out["actual"] == "radumarias/rencfs"


def test_quarantine_then_fresh_clone_uses_task_repo(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    ws = tmp_path / "opire_rencfs3"
    bad = ws / "src"
    _git_init(bad, remote="https://github.com/uytyutu/Genesis-AI-Engine.git")
    upstream = tmp_path / "upstream_rencfs"
    _git_init(upstream)

    assert workspace_matches_repository(bad, "radumarias/rencfs")["ok"] is False
    q = quarantine_workspace_safe(ws)
    assert q.get("ok") is True
    assert not ws.exists()

    ws.mkdir(parents=True)
    dest = ws / "src"
    # Local path clone (fixture) — origin will be file URL / path, so set remote after
    res = clone_repository(str(upstream), dest, timeout=60)
    assert res.get("ok") is True, res
    git = resolve_git_binary()
    assert git
    subprocess.run(
        [git, "remote", "remove", "origin"],
        cwd=dest,
        check=False,
        capture_output=True,
    )
    subprocess.run(
        [git, "remote", "add", "origin", "https://github.com/radumarias/rencfs.git"],
        cwd=dest,
        check=True,
        capture_output=True,
    )
    assert workspace_matches_repository(dest, "radumarias/rencfs")["ok"] is True


def test_push_branch_stops_on_genesis_mismatch(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    src = tmp_path / "src"
    _git_init(src, remote="https://github.com/uytyutu/Genesis-AI-Engine.git")
    with patch("swarm.farm_github_live._github_token", return_value="tok"):
        out = push_branch(
            src,
            "virtus/opire-3",
            source_owner="radumarias",
            source_repo="rencfs",
        )
    assert out["ok"] is False
    assert out["error"] == "WORKSPACE_REPOSITORY_MISMATCH"


def test_ensure_user_fork_rejects_non_fork_same_name() -> None:
    """Genesis-AI-Engine must never count as fork of itself / wrong parent."""
    with (
        patch("swarm.farm_github_live.github_login", return_value="uytyutu"),
        patch(
            "swarm.farm_github_live._api",
            return_value={
                "ok": True,
                "data": {
                    "full_name": "uytyutu/Genesis-AI-Engine",
                    "fork": False,
                    "parent": {},
                },
            },
        ),
    ):
        out = ensure_user_fork("uytyutu", "Genesis-AI-Engine")
    assert out["ok"] is False
    assert out["error"] == "fork_name_collision"


def test_ensure_user_fork_accepts_correct_parent() -> None:
    with (
        patch("swarm.farm_github_live.github_login", return_value="uytyutu"),
        patch(
            "swarm.farm_github_live._api",
            return_value={
                "ok": True,
                "data": {
                    "full_name": "uytyutu/rencfs",
                    "fork": True,
                    "parent": {"full_name": "radumarias/rencfs"},
                },
            },
        ),
    ):
        out = ensure_user_fork("radumarias", "rencfs")
    assert out["ok"] is True
    assert out["fork_full"] == "uytyutu/rencfs"
    assert out["fork_parent"] == "radumarias/rencfs"


def test_live_submit_stops_without_push_on_mismatch(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    ws = tmp_path / "ws"
    src = ws / "src"
    _git_init(src, remote="https://github.com/uytyutu/Genesis-AI-Engine.git")
    (ws / "PULL_REQUEST.md").write_text("/claim #3\n", encoding="utf-8")
    task = {
        "repository": "radumarias/rencfs",
        "issue_id": "3",
        "title": "research implementation for Windows",
        "execution": {"branch": "virtus/opire-3", "workspace": str(ws)},
    }
    with patch("swarm.farm_github_live._github_token", return_value="tok"):
        out = live_submit_draft_pr(task, ws)
    assert out["ok"] is False
    assert out["error"] == "WORKSPACE_REPOSITORY_MISMATCH"
