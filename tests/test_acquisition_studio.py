"""Mission 1.5 — Business Acquisition Studio Foundation tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.acquisition_studio_service import AcquisitionStudioService
from app.integration.context import get_integration, reset_integration
from app.integration.opportunity_service import OpportunityService
from app.integration.sales_order_service import SalesOrderService
from app.main import app


def _client(tmp_path: Path) -> TestClient:
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)
    return TestClient(app)


def test_studio_status_no_auto_send(tmp_path: Path):
    svc = AcquisitionStudioService(
        OpportunityService(tmp_path / "memory"),
        SalesOrderService(tmp_path / "memory", factory_intent=object()),
    )
    status = svc.studio_status()
    assert status["auto_send"] is False
    assert status["auto_search"] is False
    assert status["law"] == "Plan → Approve → Act"


def test_prepare_and_approval_queue(tmp_path: Path):
    opp = OpportunityService(tmp_path / "memory")
    sales = SalesOrderService(tmp_path / "memory", factory_intent=object())
    studio = AcquisitionStudioService(opp, sales)
    row = opp.create(
        {
            "source_id": "manual",
            "company_name": "Autowerkstatt Müller",
            "contact": "info@mueller.de",
            "fit_reason": "нет сайта, только Maps",
            "website_url": "http://example.com",
        }
    )
    prepared = studio.prepare_opportunity(row["id"])
    assert prepared["outreach_status"] == "pending_approval"
    assert prepared["proposed_message"]
    assert prepared["recommended_price_eur"] in (350.0, 650.0, 1200.0)
    queue = studio.approval_queue()
    assert len(queue) == 1
    assert queue[0]["company_name"] == "Autowerkstatt Müller"


def test_approve_without_outreach_enabled_marks_approved(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("GENESIS_OUTREACH_ENABLED", raising=False)
    opp = OpportunityService(tmp_path / "memory")
    sales = SalesOrderService(tmp_path / "memory", factory_intent=object())
    studio = AcquisitionStudioService(opp, sales)
    row = opp.create(
        {
            "source_id": "manual",
            "company_name": "Café Test",
            "contact": "cafe@test.de",
            "fit_reason": "устаревший сайт",
        }
    )
    studio.prepare_opportunity(row["id"])
    result = studio.approve_outreach(row["id"])
    assert result["ok"] is True
    assert result["opportunity"]["outreach_status"] == "approved"
    assert result["send_result"] is None


def test_evidence_insufficient_sample(tmp_path: Path):
    svc = AcquisitionStudioService(
        OpportunityService(tmp_path / "memory"),
        SalesOrderService(tmp_path / "memory", factory_intent=object()),
    )
    report = svc.evidence_report()
    assert report["evidence_ready"] is False
    assert report["contacted"] == 0
    assert any("5 контактов" in i for i in report["insights"])


def test_acquisition_api_status(tmp_path: Path):
    client = _client(tmp_path)
    res = client.get("/api/acquisition/status")
    assert res.status_code == 200
    body = res.json()
    assert body["version"] == "1.5-foundation"
    assert body["auto_send"] is False


def test_prepare_api_flow(tmp_path: Path):
    client = _client(tmp_path)
    create = client.post(
        "/api/opportunities",
        json={
            "source_id": "manual",
            "company_name": "Zahnarzt Pirna",
            "fit_reason": "нет HTTPS",
            "website_url": "https://example.org",
        },
    )
    assert create.status_code == 200
    opp_id = create.json()["opportunity"]["id"]
    prep = client.post(
        f"/api/acquisition/opportunities/{opp_id}/prepare",
        json={},
    )
    assert prep.status_code == 200
    assert prep.json()["opportunity"]["outreach_status"] == "pending_approval"
    queue = client.get("/api/acquisition/approval-queue")
    assert queue.status_code == 200
    assert len(queue.json()["items"]) == 1
