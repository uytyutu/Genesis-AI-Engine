"""Farm Stabilization Pass — workspace lifecycle, retry taxonomy, spider idle, queues."""

from __future__ import annotations

import json
import subprocess
import threading
import time
from pathlib import Path

import pytest

from swarm.farm_execution_engine import (
    clone_repository,
    ensure_fresh_workspace,
    resolve_git_binary,
)
from swarm.farm_queues import (
    API_FARM_QUEUE,
    BOUNTY_EXECUTION_QUEUE,
    build_farm_queues_status,
)
from swarm.farm_stabilization import (
    PERMANENT_ERROR,
    TRANSIENT_ERROR,
    WORKSPACE_CORRUPTION,
    WS_CLONING,
    WS_ORPHANED,
    assess_hunt_inputs,
    build_failure_visibility,
    classify_execution_failure,
    classify_workspace_path,
    cleanup_stale_workspaces,
    inventory_workspaces,
    is_valid_git_workspace,
    load_idle_state,
    mark_hunt_active,
    mark_idle_no_work,
    should_skip_hunt,
)
from swarm.opire_farm import OpireFarmEngine


def _init_upstream(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    git = resolve_git_binary()
    assert git
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


def test_classify_src_already_exists() -> None:
    c = classify_execution_failure(
        error="fatal: destination path '...\\src' already exists and is not an empty directory",
        error_code="",
    )
    assert c["error_class"] == WORKSPACE_CORRUPTION
    assert c["retryable"] is True
    assert c["next_action"] == "QUARANTINE_AND_RETRY"


def test_classify_permanent_repo_not_found() -> None:
    c = classify_execution_failure(error_code="repo_not_found", error="fatal: not found")
    assert c["error_class"] == PERMANENT_ERROR
    assert c["retryable"] is False


def test_classify_transient_timeout() -> None:
    c = classify_execution_failure(error="timeout", error_code="concurrent_clone")
    assert c["error_class"] == TRANSIENT_ERROR
    assert c["next_action"] == "RETRY_WITH_BACKOFF"


def test_dirty_empty_and_valid_src(tmp_path: Path) -> None:
    dirty = tmp_path / "dirty" / "src"
    dirty.mkdir(parents=True)
    (dirty / "x.txt").write_text("x", encoding="utf-8")
    assert is_valid_git_workspace(dirty) is False

    empty = tmp_path / "empty" / "src"
    empty.mkdir(parents=True)
    assert is_valid_git_workspace(empty) is False

    if not resolve_git_binary():
        pytest.skip("git missing")
    upstream = tmp_path / "up"
    _init_upstream(upstream)
    dest = tmp_path / "ws" / "src"
    assert clone_repository(str(upstream), dest, timeout=60)["ok"]
    assert is_valid_git_workspace(dest) is True


def test_interrupted_cloning_dir_quarantine(tmp_path: Path) -> None:
    root = tmp_path / "opire_workspaces"
    root.mkdir()
    cloning = root / ".cloning-abcdef12"
    cloning.mkdir()
    (cloning / "partial").write_text("x", encoding="utf-8")
    assert classify_workspace_path(cloning) == WS_CLONING
    out = cleanup_stale_workspaces(root)
    assert not cloning.exists()
    assert any(a.get("action") == "remove_temp" for a in out["actions"])


def test_orphan_workspace_quarantine_not_delete_active(tmp_path: Path) -> None:
    root = tmp_path / "opire_workspaces"
    active = root / "opire_active_job"
    orphan = root / "opire_old_orphan"
    active.mkdir(parents=True)
    (active / "src").mkdir()
    orphan.mkdir(parents=True)
    (orphan / "src").mkdir()
    (orphan / "src" / "junk").write_text("j", encoding="utf-8")
    # Force orphan age classification via mtime if needed — empty dirty → STALE/ORPHANED
    inv = inventory_workspaces(root, active_reward_ids={"opire_active_job"})
    states = {r["name"]: r["state"] for r in inv}
    assert states["opire_active_job"] == "ACTIVE"
    cleaned = cleanup_stale_workspaces(
        root, active_reward_ids={"opire_active_job"}
    )
    assert active.exists()
    # orphan should be quarantined (renamed) or removed via quarantine
    assert not orphan.exists() or any(
        a.get("name") == "opire_old_orphan" for a in cleaned["actions"]
    )


def test_failure_visibility_fields() -> None:
    vis = build_failure_visibility(
        job_id="opire:1",
        queue=BOUNTY_EXECUTION_QUEUE,
        stage="repo_intelligence",
        attempt=1,
        error="already exists and is not an empty directory",
        error_code="workspace_dirty",
        workspace="D:/ws/opire_1",
    )
    assert vis["error_class"] == WORKSPACE_CORRUPTION
    assert vis["retryable"] is True
    assert vis["next_action"] == "QUARANTINE_AND_RETRY"
    assert vis["job_id"] == "opire:1"
    assert vis["queue"] == BOUNTY_EXECUTION_QUEUE


def test_mark_execution_failed_workspace_taxonomy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("FARM_BOUNTY_ADVANCE_ON_FAIL", "0")
    eng = OpireFarmEngine(tmp_path)
    task = {
        "id": "opire:ws-exists",
        "title": "research implementation for Windows",
        "status": "executing",
        "execution_attempts": 1,
        "execution": {"stage": "repo_intelligence"},
    }
    failed = eng._mark_execution_failed(
        task,
        detail="destination path ...\\src already exists and is not an empty directory",
        reason="execution_failed",
        stage="failed",
        error_code="workspace_dirty",
    )
    assert failed["error_class"] == WORKSPACE_CORRUPTION
    assert failed["next_action"] == "QUARANTINE_AND_RETRY"
    assert failed["auto_retry_execution"] is True
    assert failed["force_fresh_workspace"] is True
    assert failed["failure"]["attempt"] == 1


def test_permanent_failure_no_retry(tmp_path: Path) -> None:
    eng = OpireFarmEngine(tmp_path)
    failed = eng._mark_execution_failed(
        {
            "id": "opire:gone",
            "execution_attempts": 1,
            "execution": {},
        },
        detail="repository not found",
        error_code="repo_not_found",
    )
    assert failed["error_class"] == PERMANENT_ERROR
    assert failed["auto_retry_execution"] is False
    assert failed["next_action"] == "FAILED"


def test_ensure_fresh_then_clone_after_dirty(tmp_path: Path) -> None:
    if not resolve_git_binary():
        pytest.skip("git missing")
    upstream = tmp_path / "up"
    _init_upstream(upstream)
    ws = tmp_path / "opire_ws"
    src = ws / "src"
    src.mkdir(parents=True)
    (src / "stale").write_text("old", encoding="utf-8")
    assert ensure_fresh_workspace(ws)["ok"]
    assert list(ws.iterdir()) == []
    assert clone_repository(str(upstream), ws / "src", timeout=60)["ok"]


def test_hunt_idle_when_no_inputs(tmp_path: Path) -> None:
    cfg = {
        "freeze_lists": True,
        "target_mode": "places_only",
        "seed_targets": [],
        "places_queries": [],
        "profitable_niches": [],
        "toloka_task_categories": [],
    }
    hunt = assess_hunt_inputs(cfg, places_configured=False)
    assert hunt["has_work"] is False
    idle1 = mark_idle_no_work(tmp_path)
    assert idle1["mode"] == "IDLE"
    assert idle1["backoff_sec"] == 8
    idle2 = mark_idle_no_work(tmp_path)
    assert idle2["backoff_sec"] == 16
    skip, st = should_skip_hunt(tmp_path)
    assert skip is True
    assert st["mode"] == "IDLE"
    active = mark_hunt_active(tmp_path)
    assert active["mode"] == "ACTIVE"
    assert load_idle_state(tmp_path)["consecutive_idle"] == 0


def test_queue_isolation_unchanged() -> None:
    status = build_farm_queues_status(None)
    assert BOUNTY_EXECUTION_QUEUE in status["queues"]
    assert API_FARM_QUEUE in status["queues"]
    assert status["bounty"]["independent_of_api_farm"] is True
    assert status["api_farm"]["independent_of_bounty"] is True
    assert status["bounty"]["queue_id"] != status["api_farm"]["queue_id"]
    assert "BOUNTY_EXECUTION_QUEUE ≠ API_FARM_QUEUE" in status["separation_ru"]


def test_api_farm_auto_publish_false() -> None:
    from swarm.farm_channels.rapidapi.publisher import auto_publish_allowed

    assert auto_publish_allowed() is False


def test_concurrent_lock_still_blocks(tmp_path: Path) -> None:
    from swarm.farm_execution_engine import FarmExecutionEngine, _lock_for_reward

    rid = "opire:lock-test"
    lock = _lock_for_reward(rid)
    assert lock.acquire(blocking=False)
    try:
        held = {"ok": False}

        def _try() -> None:
            held["ok"] = _lock_for_reward(rid).acquire(blocking=False)

        t = threading.Thread(target=_try)
        t.start()
        t.join(2)
        assert held["ok"] is False
        eng = FarmExecutionEngine(tmp_path)
        report = eng.run_pipeline(
            {"id": rid, "repository": "octocat/Hello-World", "title": "t"},
            clone=True,
            run_impl=False,
        )
        assert report.get("error") == "concurrent_clone"
        assert report.get("error_class") == TRANSIENT_ERROR
    finally:
        lock.release()


def test_spider_dashboard_idle_fields(tmp_path: Path) -> None:
    from app.integration.global_spider_service import GlobalSpiderService

    cfg = tmp_path / "global_spider_config.json"
    cfg.write_text(
        json.dumps(
            {
                "freeze_lists": True,
                "target_mode": "places_only",
                "seed_targets": [],
                "places_queries": [],
                "toloka_task_categories": [],
                "polling_interval_sec": 8,
            }
        ),
        encoding="utf-8",
    )
    spider = GlobalSpiderService(tmp_path)
    dash = spider.spider_dashboard()
    assert dash["idle"] is True
    assert dash["hunter_mode"] is False
    assert dash["idle_status"] == "WAITING_FOR_INPUT"
