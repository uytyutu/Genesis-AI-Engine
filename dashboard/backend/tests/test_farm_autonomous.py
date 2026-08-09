"""Farm AUTO-RUN — drain QUEUED, auto-approve GO≥80, auto-submit, watchdog."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from swarm.farm_autonomous import (
    MAX_EXECUTION_ATTEMPTS,
    run_autonomous_tick,
)
from swarm.opire_farm import OpireFarmEngine


def _iso_ago(seconds: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat()


def test_watchdog_heals_queued_without_ceo_start(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FARM_AUTONOMOUS", "1")
    monkeypatch.setenv("FARM_AUTO_APPROVE", "0")
    monkeypatch.setenv("FARM_AUTO_SUBMIT_PR", "0")
    eng = OpireFarmEngine(tmp_path)
    state = {
        "tasks": {
            "opire:stuck": {
                "id": "opire:stuck",
                "title": "research implementation for Windows",
                "status": "executing",
                "pipeline_state": "QUEUED",
                "updated_at": _iso_ago(120),
                "execution": {"ok": True, "stage": "queued"},
                "execution_attempts": 0,
            }
        }
    }
    eng._save(state)

    starts: list[str] = []

    def _start(rid: str, *, clone: bool = True, _auto_depth: int = 0):
        starts.append(rid)
        st = eng._load()
        t = st["tasks"][rid]
        t["status"] = "executing"
        t["pipeline_state"] = "CLONING"
        t["execution"] = {
            "ok": True,
            "stage": "repo_intelligence",
            "stages": {"repo_intelligence": {"ok": True}},
        }
        st["tasks"][rid] = t
        eng._save(st)
        return {"ok": True, "task": t}

    out = run_autonomous_tick(eng, max_actions=5, start_execution=_start)
    types = [a["type"] for a in out["actions"]]
    assert "watchdog_heal" in types or "drain_start" in types
    # Drain must start without CEO button
    assert starts == ["opire:stuck"] or any(
        a.get("type") == "drain_start" for a in out["actions"]
    )
    # Second tick after heal+drain path
    if not starts:
        out2 = run_autonomous_tick(eng, max_actions=5, start_execution=_start)
        assert starts, out2


def test_auto_approve_go_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FARM_AUTONOMOUS", "1")
    monkeypatch.setenv("FARM_AUTO_APPROVE", "1")
    monkeypatch.setenv("FARM_AUTO_SUBMIT_PR", "0")
    monkeypatch.setenv("FARM_AUTO_EXECUTE_ON_APPROVE", "0")
    eng = OpireFarmEngine(tmp_path)
    eng._save(
        {
            "tasks": {},
            "last_scan": {
                "candidates": [
                    {
                        "id": "opire:go-1",
                        "title": "Fix typo in README",
                        "overall_confidence_pct": 87,
                        "estimated_hours": 1,
                        "competitors": 0,
                        "repo_status": "ok",
                        "supported_languages": ["python"],
                        "url": "https://github.com/acme/x/issues/1",
                        "preflight": {
                            "go": True,
                            "verdict": "GO",
                            "auto_execute_allowed": True,
                            "approve_allowed": True,
                        },
                    },
                    {
                        "id": "opire:review-1",
                        "title": "Unclear large feature",
                        "overall_confidence_pct": 60,
                        "preflight": {
                            "go": False,
                            "verdict": "REVIEW",
                            "auto_execute_allowed": False,
                            "approve_allowed": True,
                        },
                    },
                ]
            },
        }
    )

    decided: list[str] = []

    def _decide(rid: str, decision: str, *, note: str = ""):
        decided.append(rid)
        st = eng._load()
        st.setdefault("tasks", {})[rid] = {
            "id": rid,
            "status": "ceo_approved",
            "pipeline_state": "QUEUED",
            "pending_execution": True,
            "title": "auto",
        }
        eng._save(st)
        return {"ok": True, "task": st["tasks"][rid]}

    out = run_autonomous_tick(
        eng,
        max_actions=3,
        decide=_decide,
        start_execution=lambda *a, **k: {"ok": True},
    )
    assert any(a.get("type") == "auto_approve" for a in out["actions"])
    assert decided == ["opire:go-1"]


def test_auto_submit_after_draft(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FARM_AUTONOMOUS", "1")
    monkeypatch.setenv("FARM_AUTO_APPROVE", "0")
    monkeypatch.setenv("FARM_AUTO_SUBMIT_PR", "1")
    eng = OpireFarmEngine(tmp_path)
    eng._save(
        {
            "tasks": {
                "opire:draft": {
                    "id": "opire:draft",
                    "status": "draft_pr",
                    "title": "patch ready",
                    "updated_at": _iso_ago(5),
                    "execution": {
                        "patch_ready": True,
                        "stages": {
                            "implementation": {"files_touched": ["a.py"]},
                        },
                    },
                }
            }
        }
    )
    submits: list[str] = []

    def _submit(rid: str, *, note: str = "", live: bool = True):
        submits.append(rid)
        st = eng._load()
        t = st["tasks"][rid]
        t["status"] = "pr_submitted"
        t["pr_url"] = "https://github.com/acme/x/pull/1"
        t["auto_submit_done"] = True
        st["tasks"][rid] = t
        eng._save(st)
        return {"ok": True, "task": t}

    out = run_autonomous_tick(
        eng,
        max_actions=3,
        submit_pr=_submit,
        start_execution=lambda *a, **k: {"ok": True},
    )
    assert any(a.get("type") == "auto_submit" and a.get("ok") for a in out["actions"])
    assert submits == ["opire:draft"]
    # Idempotent — second tick must not duplicate
    out2 = run_autonomous_tick(
        eng,
        max_actions=3,
        submit_pr=_submit,
        start_execution=lambda *a, **k: {"ok": True},
    )
    assert submits == ["opire:draft"]
    assert not any(a.get("type") == "auto_submit" and a.get("ok") for a in out2["actions"])


def test_max_attempts_hard_skip_no_infinite(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("FARM_AUTONOMOUS", "1")
    monkeypatch.setenv("FARM_AUTO_APPROVE", "0")
    monkeypatch.setenv("FARM_AUTO_SUBMIT_PR", "0")
    eng = OpireFarmEngine(tmp_path)
    eng._save(
        {
            "tasks": {
                "opire:dead": {
                    "id": "opire:dead",
                    "status": "executing",
                    "pipeline_state": "QUEUED",
                    "updated_at": _iso_ago(200),
                    "execution": {"stage": "queued"},
                    "execution_attempts": MAX_EXECUTION_ATTEMPTS,
                }
            }
        }
    )
    starts: list[str] = []
    out = run_autonomous_tick(
        eng,
        max_actions=5,
        start_execution=lambda rid, **k: starts.append(rid) or {"ok": True},
    )
    assert any(a.get("type") == "watchdog_skip" for a in out["actions"])
    assert starts == []
    assert eng._load()["tasks"]["opire:dead"]["status"] == "skipped"


def test_cloning_heartbeat_on_start(tmp_path: Path, monkeypatch) -> None:
    """start_execution must leave CLONING heartbeat before blocking pipeline."""
    eng = OpireFarmEngine(tmp_path)
    monkeypatch.setenv("FARM_AUTO_SUBMIT_PR", "0")
    eng._save(
        {
            "tasks": {
                "opire:hb": {
                    "id": "opire:hb",
                    "status": "ceo_approved",
                    "repository": "acme/demo",
                    "title": "hb",
                    "url": "https://github.com/acme/demo/issues/1",
                }
            }
        }
    )

    heartbeats: list[dict] = []

    def _fake_pipeline(task, *, clone=True, run_impl=True):
        # Observe state as saved before pipeline
        cur = eng._load()["tasks"]["opire:hb"]
        heartbeats.append(
            {
                "pipeline_state": cur.get("pipeline_state"),
                "stage": (cur.get("execution") or {}).get("stage"),
            }
        )
        return {
            "ok": False,
            "stage": "failed",
            "error": "clone_failed",
            "stages": {},
        }

    import swarm.opire_farm as mod
    import swarm.opire_issue_intel as intel

    class _E:
        def __init__(self, *_a, **_k):
            pass

        def run_pipeline(self, task, *, clone=True, run_impl=True):
            return _fake_pipeline(task, clone=clone, run_impl=run_impl)

    monkeypatch.setattr(mod, "FarmExecutionEngine", _E)
    monkeypatch.setattr(
        intel,
        "apply_sniper_to_candidate",
        lambda c, timeout=12.0: {
            **c,
            "repo_status": "ok",
            "recommendation": "TAKE",
            "blockers": [],
        },
    )
    monkeypatch.setattr(
        "swarm.farm_opire_sync.maybe_post_try",
        lambda *_a, **_k: {"ok": True, "skipped": True},
    )

    eng.start_execution("opire:hb", clone=True)
    assert heartbeats
    assert heartbeats[0]["pipeline_state"] == "CLONING"
    assert heartbeats[0]["stage"] == "repo_intelligence"
