"""Public Launch v1 checklist tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.integration.public_launch_service import PublicLaunchService
from app.main import app


def test_public_launch_checklist_local(tmp_path: Path):
    svc = PublicLaunchService(tmp_path / "memory")
    data = svc.run()
    assert data["sprint"] == "Public Launch v1"
    assert len(data["checks"]) >= 10
    assert data["launch_ready"] is False


def test_public_launch_api(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)
    client = TestClient(app)
    res = client.get("/api/owner/public-launch")
    assert res.status_code == 200
    body = res.json()
    assert body["sprint"] == "Public Launch v1"
    assert "kpi" in body
    reset_integration()
