"""Integration Layer API tests — live Brain, isolated memory per test."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(ROOT))

from app.integration.context import get_integration, reset_integration  # noqa: E402
from app.main import app  # noqa: E402
from app.schemas import CreateTaskRequest  # noqa: E402

httpx = pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture
def memory_dir(tmp_path):
    reset_integration()
    path = tmp_path / "memory"
    get_integration(path)
    yield path
    reset_integration()


@pytest.fixture
def client(memory_dir) -> TestClient:
    return TestClient(app)


def test_live_modules_show_core_online(client: TestClient) -> None:
    response = client.get("/api/modules")
    modules = {m["id"]: m["status"] for m in response.json()["modules"]}
    assert modules["kernel"] == "online"
    assert modules["brain"] == "online"
    assert modules["queue"] == "online"
    assert modules["audit"] == "online"
    assert modules["factory"] == "online"


def test_create_task_and_list(client: TestClient) -> None:
    created = client.post("/api/tasks", json={"name": "ui-test-job"})
    assert created.status_code == 200
    task_id = created.json()["task_id"]

    listed = client.get("/api/tasks")
    tasks = listed.json()["tasks"]
    assert any(t["task_id"] == task_id for t in tasks)
    assert any(t["name"] == "ui-test-job" for t in tasks)


def test_run_next_completes_task(client: TestClient) -> None:
    client.post("/api/tasks", json={"name": "run-me"})
    result = client.post("/api/tasks/run-next")
    assert result.status_code == 200
    data = result.json()
    assert data["result"] == "ok"
    assert data["duration_ms"] is not None


def test_cancel_queued_task(client: TestClient) -> None:
    created = client.post("/api/tasks", json={"name": "cancel-me"})
    task_id = created.json()["task_id"]

    cancel = client.post(f"/api/tasks/{task_id}/cancel")
    assert cancel.status_code == 200

    tasks = client.get("/api/tasks").json()["tasks"]
    task = next(t for t in tasks if t["task_id"] == task_id)
    assert task["status"] == "cancelled"


def test_pause_shows_degraded_brain(client: TestClient) -> None:
    client.post("/api/control/pause")
    modules = client.get("/api/modules").json()["modules"]
    brain = next(m for m in modules if m["id"] == "brain")
    assert brain["status"] == "degraded"

    status = client.get("/api/status").json()
    assert status["paused"] is True


def test_api_status_responds_quickly(client: TestClient) -> None:
    import time

    elapsed = []
    for _ in range(5):
        t0 = time.perf_counter()
        response = client.get("/api/status")
        elapsed.append((time.perf_counter() - t0) * 1000)
        assert response.status_code == 200
        body = response.json()
        assert body["name"] == "Genesis ABOS"
        assert body.get("uptime_sec") is not None

    assert max(elapsed) < 200, f"/api/status too slow: {max(elapsed):.0f}ms"


def test_integration_full_cycle(client: TestClient) -> None:
    """Create → list → run → audit activity."""
    client.post("/api/tasks", json={"name": "cycle-a"})
    client.post("/api/tasks", json={"name": "cycle-b"})
    client.post("/api/tasks/run-next")

    queue = client.get("/api/queue").json()
    assert queue["completed"] >= 1
    assert queue["pending"] >= 1

    activity = client.get("/api/activity").json()["events"]
    assert len(activity) >= 1


def test_demo_mode_creates_and_runs_five_tasks(client: TestClient) -> None:
    response = client.post("/api/demo/run")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks_created"] == 5
    assert data["tasks_completed"] == 5
    assert data["tasks_failed"] == 0
    assert len(data["task_ids"]) == 5

    queue = client.get("/api/queue").json()
    assert queue["completed"] >= 5
