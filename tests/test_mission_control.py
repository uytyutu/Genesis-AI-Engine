"""Mission Control API tests."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_mission_control_live(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text(
        '{"owner_name": "Рамиш", "company_founded_at": "2026-01-01T00:00:00+00:00"}',
        encoding="utf-8",
    )
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/mission-control")
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "Genesis Company"
    assert data["owner_name"] == "Рамиш"
    assert data["company_days"] >= 1
    assert len(data["digital_employees"]) == 7
    assert data["demo_mode"] is False
    assert "valuation_methodology" in data
    assert "system_status_label" in data
    assert "decisions_needed" in data
    journey = data.get("first_customer_journey")
    assert journey is not None
    assert journey["title"] == "До первого клиента"
    assert journey["total_count"] >= 5
    assert "morning_summary" in data
    assert data["morning_summary"]["journey_progress_percent"] >= 0
    assert len(data["narrative_feed"]) >= 2
    assert len(data["income_goals"]) == 4
    assert data["income_goals"][0]["id"] == "today"
    readiness = data["company_readiness"]
    assert readiness["total_count"] >= 5
    assert 0 <= readiness["percent"] <= 100
    assert len(readiness["items"]) == readiness["total_count"]
    ops = data["company_operations"]
    assert "uptime_label" in ops
    assert ops["last_downtime_label"] in ("0", "сейчас", "не было", "давно")
    assert "systems_status_label" in ops

    reset_integration()


def test_mission_control_demo_mode(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text('{"owner_name": "Рамиш"}', encoding="utf-8")
    get_integration(memory)

    client = TestClient(app)
    on = client.post("/api/owner/demo-mode", json={"enabled": True})
    assert on.status_code == 200
    assert on.json()["demo_mode"] is True

    res = client.get("/api/owner/mission-control")
    data = res.json()
    assert data["demo_mode"] is True
    assert data["company_value_eur"] > 0
    assert data["revenue_today_eur"] == 341.0
    assert data["company_readiness"]["percent"] == 71
    assert data["company_operations"]["uptime_label"] == "12 ч 41 мин"
    assert len(data["overnight_events"]) >= 5
    assert data["company_history"]["total_revenue_eur"] > 0

    off = client.post("/api/owner/demo-mode", json={"enabled": False})
    assert off.json()["demo_mode"] is False

    reset_integration()
