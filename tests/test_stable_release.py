"""Stable Release v3 — history, rollback, release notes."""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.stable_release import (
    STATUS_ROLLBACK_AVAILABLE,
    STATUS_STABLE_RELEASE,
    activate_stable_release,
    compute_release_status,
    read_active_release,
    read_release_history,
    release_snapshot_ready,
    rollback_to_previous_release,
    working_matches_active_release,
    write_display_payload,
)


def _write_min_next(nxt: Path, build_id: str = "rel-test-1") -> None:
    nxt.mkdir(parents=True, exist_ok=True)
    (nxt / "routes-manifest.json").write_text("{}", encoding="utf-8")
    (nxt / "BUILD_ID").write_text(build_id, encoding="utf-8")
    (nxt / "server").mkdir(parents=True, exist_ok=True)
    (nxt / "server" / "pages-manifest.json").write_text("{}", encoding="utf-8")
    (nxt / "server" / "app").mkdir(parents=True, exist_ok=True)
    (nxt / "server" / "app" / "page.js").write_text("//", encoding="utf-8")


def _patch_paths(monkeypatch: pytest.MonkeyPatch, root: Path, fe: Path, mem: Path) -> None:
    monkeypatch.setattr("launcher.stable_release.memory_dir", lambda _=None: mem)
    monkeypatch.setattr("launcher.stable_release.frontend_dir", lambda _=None: fe)
    monkeypatch.setattr("launcher.stable_release.frontend_build_integrity", lambda _=None: True)
    monkeypatch.setattr("launcher.stable_release.read_git_commit_short", lambda _=None: "a92cac7")


def test_activate_history_and_rollback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fe = tmp_path / "dashboard" / "frontend"
    mem = tmp_path / "memory"
    mem.mkdir(parents=True)
    _patch_paths(monkeypatch, tmp_path, fe, mem)

    _write_min_next(fe / ".next", "build-v1")
    ok1, _ = activate_stable_release(
        tmp_path,
        label="2026.07.08",
        title="Legal & Trust Foundation",
        product_blocks=["Legal & Trust"],
        approved_by="CEO PASS",
    )
    assert ok1 is True
    r1 = read_active_release(tmp_path)
    assert r1 is not None
    assert r1.title == "Legal & Trust Foundation"
    assert r1.git_commit == "a92cac7"

    _write_min_next(fe / ".next", "build-v2")
    ok2, _ = activate_stable_release(
        tmp_path,
        label="2026.07.10",
        title="Project Platform v1",
        product_blocks=["Project Platform"],
    )
    assert ok2 is True
    history = read_release_history(tmp_path)
    assert len(history) >= 1
    assert history[0].title == "Legal & Trust Foundation"

    active = read_active_release(tmp_path)
    assert active is not None
    assert active.title == "Project Platform v1"

    status = compute_release_status(tmp_path)
    assert status["rollback_available"] is True

    ok_rb, msg = rollback_to_previous_release(tmp_path)
    assert ok_rb is True
    assert "Legal" in msg or "2026.07.08" in msg
    rolled = read_active_release(tmp_path)
    assert rolled is not None
    assert rolled.title == "Legal & Trust Foundation"
    assert working_matches_active_release(tmp_path)


def test_display_payload_written(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fe = tmp_path / "dashboard" / "frontend"
    mem = tmp_path / "memory"
    mem.mkdir(parents=True)
    _patch_paths(monkeypatch, tmp_path, fe, mem)
    _write_min_next(fe / ".next")
    activate_stable_release(tmp_path, title="Product Truth", label="2026.07.07")
    path = write_display_payload(tmp_path)
    assert path.is_file()
    data = path.read_text(encoding="utf-8")
    assert "stable_release" in data
    assert "Product Truth" in data


def test_release_status_stable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fe = tmp_path / "dashboard" / "frontend"
    mem = tmp_path / "memory"
    _patch_paths(monkeypatch, tmp_path, fe, mem)
    _write_min_next(fe / ".next", "only")
    activate_stable_release(tmp_path, title="Solo")
    status = compute_release_status(tmp_path)
    assert status["status"] in (STATUS_STABLE_RELEASE, STATUS_ROLLBACK_AVAILABLE)
    assert release_snapshot_ready(tmp_path)
