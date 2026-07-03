"""Opportunity Engine v0 — skeleton tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.integration.opportunity_service import OpportunityService
from app.main import app


def _client(tmp_path: Path) -> TestClient:
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)
    return TestClient(app)


def test_opportunity_snapshot_honest_zeros(tmp_path: Path):
    svc = OpportunityService(tmp_path / "memory")
    snap = svc.snapshot()
    assert snap["engine_active"] is False
    assert snap["found_today"] == 0


def test_record_opportunity_activates_engine(tmp_path: Path):
    svc = OpportunityService(tmp_path / "memory")
    svc.record_opportunity("Автосервис без сайта", "google_maps")
    snap = svc.snapshot()
    assert snap["found_today"] >= 1
    assert snap["queue_preview"][0]["title"] == "Автосервис без сайта"


def test_source_registry_manual_and_maps_enabled(tmp_path: Path):
    svc = OpportunityService(tmp_path / "memory")
    sources = {s["id"]: s for s in svc.list_sources()}
    assert sources["manual"]["enabled"] is True
    assert sources["google_maps"]["enabled"] is True
    assert sources["reddit"]["enabled"] is False
    assert sources["facebook"]["enabled"] is False


def test_create_and_update_opportunity(tmp_path: Path):
    svc = OpportunityService(tmp_path / "memory")
    row = svc.create(
        {
            "source_id": "google_maps",
            "company_name": "Café Sonne",
            "contact": "+49 111",
            "fit_reason": "Нет сайта, только Google Maps",
            "potential_value_eur": 650,
        }
    )
    assert row["id"].startswith("opp-")
    assert row["score"] > 0
    assert row["status"] == "new"

    updated = svc.update(row["id"], {"status": "contacted"})
    assert updated["status"] == "contacted"


def test_disabled_source_rejected(tmp_path: Path):
    svc = OpportunityService(tmp_path / "memory")
    try:
        svc.create(
            {
                "source_id": "reddit",
                "company_name": "Test Co",
            }
        )
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert str(e) == "source_disabled"


def test_morning_dashboard_counts(tmp_path: Path):
    svc = OpportunityService(tmp_path / "memory")
    svc.create(
        {
            "source_id": "manual",
            "company_name": "A",
            "potential_value_eur": 350,
        }
    )
    svc.create(
        {
            "source_id": "google_maps",
            "company_name": "B",
            "potential_value_eur": 650,
        }
    )
    dash = svc.morning_dashboard()
    assert dash["total_today"] == 2
    assert dash["potential_value_eur"] == 1000.0
    assert len(dash["top_today"]) == 2


def test_api_opportunities_flow(tmp_path: Path):
    client = _client(tmp_path)

    sources = client.get("/api/opportunities/sources")
    assert sources.status_code == 200
    body = sources.json()
    assert any(s["id"] == "google_maps" and s["enabled"] for s in body["sources"])
    assert any(t["id"] == "lead" for t in body["types"])

    created = client.post(
        "/api/opportunities",
        json={
            "source_id": "google_maps",
            "company_name": "Werkstatt Klein",
            "fit_reason": "Устаревший сайт",
            "potential_value_eur": 650,
        },
    )
    assert created.status_code == 200
    opp_id = created.json()["opportunity"]["id"]

    listed = client.get("/api/opportunities")
    assert listed.status_code == 200
    assert any(o["id"] == opp_id for o in listed.json()["opportunities"])

    dash = client.get("/api/opportunities/dashboard")
    assert dash.status_code == 200
    assert dash.json()["total_today"] >= 1

    patched = client.patch(
        f"/api/opportunities/{opp_id}",
        json={"status": "proposed", "proposed_message": "Здравствуйте! Мы делаем сайты…"},
    )
    assert patched.status_code == 200
    assert patched.json()["opportunity"]["status"] == "proposed"

    blocked = client.post(
        "/api/opportunities",
        json={"source_id": "facebook", "company_name": "X"},
    )
    assert blocked.status_code == 400
