"""Regression: Opire Clone must survive leftover non-empty src workspace."""

from __future__ import annotations

import subprocess
import threading
from pathlib import Path

import pytest

from swarm.farm_execution_engine import (
    classify_clone_error,
    clone_repository,
    ensure_fresh_workspace,
    remove_path_robust,
    resolve_git_binary,
)


def _init_upstream(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git = resolve_git_binary()
    assert git, "git binary required for clone regression test"
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
    (repo / "README.md").write_text("# bounty fixture\n", encoding="utf-8")
    subprocess.run([git, "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        [git, "commit", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_classify_workspace_dirty() -> None:
    c = classify_clone_error(
        "fatal: destination path 'D:/x/src' already exists and is not an empty directory."
    )
    assert c["code"] == "workspace_dirty"


def test_ensure_fresh_workspace_clears_dirty_src(tmp_path: Path) -> None:
    ws = tmp_path / "opire_01HWX4P9F1935V3ZXN4TY7VDEQ"
    src = ws / "src"
    src.mkdir(parents=True)
    (src / "leftover.txt").write_text("stale", encoding="utf-8")
    out = ensure_fresh_workspace(ws)
    assert out["ok"] is True
    assert ws.is_dir()
    assert list(ws.iterdir()) == []
    assert not src.exists()


def test_clone_succeeds_when_src_already_exists_non_empty(tmp_path: Path) -> None:
    """Exact production failure mode: leftover src → git refuses → now OK."""
    if not resolve_git_binary():
        pytest.skip("git not available")
    upstream = tmp_path / "upstream"
    _init_upstream(upstream)
    dest = tmp_path / "ws" / "src"
    dest.mkdir(parents=True)
    (dest / "stale_marker.txt").write_text("from previous failed clone", encoding="utf-8")
    assert dest.is_dir() and any(dest.iterdir())

    res = clone_repository(str(upstream), dest, timeout=60)
    assert res.get("ok") is True, res
    assert (dest / ".git").is_dir()
    assert (dest / "README.md").is_file()
    assert not (dest / "stale_marker.txt").exists()


def test_clone_idempotent_second_call(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git not available")
    upstream = tmp_path / "upstream"
    _init_upstream(upstream)
    dest = tmp_path / "ws" / "src"
    first = clone_repository(str(upstream), dest, timeout=60)
    assert first.get("ok") is True, first
    second = clone_repository(str(upstream), dest, timeout=60)
    assert second.get("ok") is True, second
    assert (dest / "README.md").is_file()


def test_concurrent_clone_lock_blocks_second(tmp_path: Path) -> None:
    from swarm.farm_execution_engine import FarmExecutionEngine, _lock_for_reward

    eng = FarmExecutionEngine(tmp_path)
    rid = "opire:01HWX4P9F1935V3ZXN4TY7VDEQ"
    lock = _lock_for_reward(rid)
    assert lock.acquire(blocking=False)
    try:
        held = {"second": False}

        def _try() -> None:
            held["second"] = _lock_for_reward(rid).acquire(blocking=False)

        t = threading.Thread(target=_try)
        t.start()
        t.join(timeout=2)
        assert held["second"] is False
        # Pipeline should report concurrent_clone when lock held
        report = eng.run_pipeline(
            {
                "id": rid,
                "repository": "octocat/Hello-World",
                "title": "coverage empty list",
            },
            clone=True,
            run_impl=False,
        )
        assert report.get("ok") is False
        assert report.get("error") == "concurrent_clone"
    finally:
        lock.release()


def test_remove_path_robust_ok_missing(tmp_path: Path) -> None:
    missing = tmp_path / "nope"
    assert remove_path_robust(missing)["ok"] is True
