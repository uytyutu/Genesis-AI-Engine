"""AI Hub service tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_ai_hub_create_approve_flow(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    create = client.post(
        "/api/ai-hub/tasks",
        json={
            "input_text": "Добавь систему инвентаря в Perfect Pallet",
            "project_id": "perfect-pallet",
        },
    )
    assert create.status_code == 200
    task = create.json()["task"]
    assert task["phase"] == "awaiting_approve"
    assert task["project_id"] == "perfect-pallet"
    assert len(task["plan"]) >= 3

    approve = client.post(
        f"/api/ai-hub/tasks/{task['id']}/approve",
        json={"auto_open": False},
    )
    assert approve.status_code == 200
    approved = approve.json()["task"]
    assert approved["phase"] in ("executing", "dispatch")
    assert approved["cursor_task_id"]

    providers = client.get("/api/ai-hub/providers")
    assert providers.status_code == 200
    assert providers.json()["default_development_provider"] == "cursor-tool"

    workspace = client.get("/api/dev/workspace")
    assert workspace.status_code == 200
    assert any(p["id"] == "genesis" for p in workspace.json()["projects"])

    reset_integration()
