"""Growth Center API tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_growth_center_live(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/growth")
    assert res.status_code == 200
    data = res.json()
    assert data["users_growth_percent"] == 0.0
    assert "бизнеса" in data["data_source_note"].lower() or "пользователей" in data["data_source_note"].lower()

    reset_integration()


def test_growth_center_demo(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    client.post("/api/owner/demo-mode", json={"enabled": True})
    data = client.get("/api/owner/growth").json()
    assert data["demo_mode"] is True
    assert data["users_growth_percent"] == 12.0
    assert data["cac_change_percent"] < 0

    reset_integration()
