"""System Check API tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_system_check_endpoint(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/system-check")
    assert res.status_code == 200
    data = res.json()
    assert "technical_checks" in data
    assert "business_checks" in data
    assert len(data["technical_checks"]) >= 10
    assert len(data["business_checks"]) >= 5
    kernel = next(c for c in data["technical_checks"] if c["id"] == "kernel")
    assert kernel["icon"] == "✔"

    reset_integration()
