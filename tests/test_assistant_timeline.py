"""Genesis Assistant tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_assistant_what_next(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post("/api/assistant/ask", json={"question": "Что мне делать дальше?"})
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "genesis"
    assert "landing" in data["answer"].lower() or "создайте" in data["answer"].lower()

    reset_integration()


def test_timeline_endpoint(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/timeline")
    assert res.status_code == 200
    data = res.json()
    assert 0 < data["progress_percent"] < 100
    assert any(m["id"] == "factory" and m["status"] == "pending" for m in data["milestones"])

    reset_integration()


def test_assistant_english(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/assistant/ask",
        json={"question": "What should I do next?", "locale": "en"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["source"] == "genesis"
    assert "recommend" in data["answer"].lower() or "product" in data["answer"].lower()

    reset_integration()
