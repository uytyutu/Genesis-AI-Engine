"""Cursor handoff API — R0.5 clipboard mode."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_cursor_status(tmp_path: Path):
    reset_integration()
    get_integration(tmp_path / "memory")
    client = TestClient(app)
    res = client.get("/api/cursor/status")
    assert res.status_code == 200
    data = res.json()
    assert data["mode"] == "semi_auto"
    assert data["bridge_ready"] is False
    reset_integration()


def test_cursor_handoff_builds_prompt(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/cursor/handoff",
        json={"kind": "task", "task_note": "Исправить Factory"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "Исправить Factory" in data["prompt"]
    assert data["chars"] > 100
    assert data.get("task") is not None
    assert data["task"]["task_id"]
    assert (memory / "cursor_last_handoff.json").is_file()
    assert (memory / "cursor_tasks.json").is_file()

    active = client.get("/api/cursor/task/active")
    assert active.status_code == 200
    assert active.json()["task"]["task_id"] == data["task"]["task_id"]

    reset_integration()


def test_cursor_verify_task(monkeypatch, tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)
    client = TestClient(app)
    client.post("/api/cursor/handoff", json={"kind": "task", "task_note": "test", "auto_open": False})

    class _Result:
        returncode = 0
        stdout = "92 passed"
        stderr = ""

    monkeypatch.setattr("app.integration.cursor_handoff_service.subprocess.run", lambda *a, **k: _Result())

    res = client.post("/api/cursor/task/verify")
    assert res.status_code == 200
    body = res.json()
    assert "task" in body
    assert body["task"]["state"] in ("ready", "failed")

    reset_integration()


def test_cursor_tasks_and_history(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)
    client = TestClient(app)

    client.post(
        "/api/cursor/handoff",
        json={"kind": "status", "task_note": "sync", "auto_open": False},
    )
    client.post(
        "/api/cursor/handoff",
        json={"kind": "task", "task_note": "Factory fix", "auto_open": False},
    )

    tasks = client.get("/api/cursor/tasks")
    assert tasks.status_code == 200
    body = tasks.json()
    assert len(body["tasks"]) >= 1

    history = client.get("/api/cursor/history")
    assert history.status_code == 200
    assert len(history.json()["items"]) >= 2

    active = body["tasks"][0]
    assert "progress_is_estimated" in active
    if active["state"] == "awaiting_cursor":
        assert active["progress_percent"] is None

    reset_integration()
    reset_integration()
    get_integration(tmp_path / "memory")
    client = TestClient(app)
    res = client.get("/api/owner/mission-control")
    assert res.status_code == 200
    journey = res.json().get("first_revenue_journey")
    assert journey is not None
    assert journey["title"] == "До первого дохода"
    assert len(journey["steps"]) == 5

    opp = res.json().get("opportunity_snapshot")
    assert opp is not None
    assert opp["found_today"] == 0
    assert opp["engine_active"] is False

    reset_integration()
