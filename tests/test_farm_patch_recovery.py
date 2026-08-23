"""Implementation → patch: recover real git diff from workspace."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from swarm.farm_execution_engine import (
    detect_workspace_file_changes,
    recover_patch_from_workspace,
    resolve_git_binary,
)


def _git(cwd: Path, *args: str) -> None:
    git = resolve_git_binary()
    assert git
    subprocess.run([git, *args], cwd=cwd, check=True, capture_output=True)


def _repo_with_base(tmp: Path) -> Path:
    repo = tmp / "src"
    repo.mkdir(parents=True)
    git = resolve_git_binary()
    assert git, "git required"
    _git(repo, "init")
    _git(repo, "config", "user.email", "farm@test.local")
    _git(repo, "config", "user.name", "Farm Test")
    (repo / "README.md").write_text("# base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")
    return repo


def test_detect_no_changes(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    repo = _repo_with_base(tmp_path)
    det = detect_workspace_file_changes(repo)
    assert det["ok"] is True
    assert det["has_changes"] is False


def test_detect_modified_file(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    repo = _repo_with_base(tmp_path)
    (repo / "README.md").write_text("# changed\n", encoding="utf-8")
    det = detect_workspace_file_changes(repo)
    assert det["has_changes"] is True
    assert any("README" in f for f in det["files"])


def test_detect_new_file(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    repo = _repo_with_base(tmp_path)
    (repo / "fix.py").write_text("print('ok')\n", encoding="utf-8")
    det = detect_workspace_file_changes(repo)
    assert det["has_changes"] is True
    assert "fix.py" in det["files"]


def test_recover_patch_when_impl_forgot_files_touched(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    repo = _repo_with_base(tmp_path)
    (repo / "handler.py").write_text("def fix():\n    return 1\n", encoding="utf-8")
    git = resolve_git_binary()
    assert git
    impl: dict = {
        "ok": True,
        "mode": "needs_external",
        "files_touched": [],
        "message_ru": "патч не получен",
    }
    report: dict = {"stages": {"implementation": impl, "commit": {"ok": False, "skipped": True}}}
    out = recover_patch_from_workspace(
        src=repo,
        git=git,
        impl=impl,
        report=report,
        title="Improve error when coverage empty",
        issue_id="1",
    )
    assert out["recovered"] is True
    assert "handler.py" in (out.get("files") or [])
    assert report["stages"]["implementation"]["files_touched"]
    assert report["stages"]["implementation"].get("patch_recovered_from_git") is True
    assert report["stages"]["commit"].get("ok") is True


def test_recover_no_changes_is_honest(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    repo = _repo_with_base(tmp_path)
    git = resolve_git_binary()
    assert git
    impl = {"ok": True, "mode": "needs_external", "files_touched": []}
    report: dict = {"stages": {"implementation": impl}}
    out = recover_patch_from_workspace(
        src=repo,
        git=git,
        impl=impl,
        report=report,
        title="noop",
        issue_id="2",
    )
    assert out["recovered"] is False
    assert out.get("reason") == "no_changes"
