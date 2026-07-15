"""Mission 2 — Business Health dashboard."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.integration.business_health_service import BusinessHealthService
from app.integration.opportunity_discovery_engine import record_lost_reason
from app.integration.opportunity_service import OpportunityService


def _seed_row(**overrides) -> dict:
    now = datetime.now(timezone.utc).isoformat()
    base = {
        "id": "opp-bh-1",
        "source_id": "manual",
        "opportunity_type": "lead",
        "company_name": "Test GmbH",
        "status": "new",
        "found_at": now,
        "updated_at": now,
        "score": 55,
        "site_analysis": {"issues": ["Kein Seitentitel"], "issue_count": 1},
    }
    base.update(overrides)
    return base


@pytest.fixture
def health_ctx(tmp_path: Path):
    opp = OpportunityService(tmp_path)
    svc = BusinessHealthService(tmp_path, opp)
    return opp, svc


def test_business_health_empty(health_ctx):
    _, svc = health_ctx
    dash = svc.dashboard()
    assert dash["mission"].startswith("Mission 2")
    assert dash["kpis"]["conversations"]["target"] == 10
    assert dash["kpis"]["payments"]["current"] == 0
    assert dash["funnel_week"]["companies_found"] == 0


def test_business_health_counts_from_journal(health_ctx):
    opp, svc = health_ctx
    a = opp.create({"source_id": "manual", "company_name": "Alpha"})
    b = opp.create({"source_id": "manual", "company_name": "Beta"})
    opp.update(a["id"], {"status": "contacted"})
    opp.update(b["id"], {"status": "proposed"})
    dash = svc.dashboard()
    assert dash["kpis"]["conversations"]["auto"] >= 1
    assert dash["kpis"]["proposals"]["auto"] >= 1


def test_manual_bump(health_ctx):
    _, svc = health_ctx
    dash = svc.bump_manual("conversations", 1)
    assert dash["kpis"]["conversations"]["manual"] == 1
    assert dash["kpis"]["conversations"]["current"] == 1


def test_weekly_review_lost_reason(health_ctx):
    opp, svc = health_ctx
    now = datetime.now(timezone.utc).isoformat()
    row = opp.create(
        {
            "source_id": "manual",
            "company_name": "Lost Co",
            "status": "lost",
            "found_at": now,
            "updated_at": now,
            "site_analysis": {"issues": ["OCR fehlt"], "issue_count": 2},
        }
    )
    record_lost_reason(
        opportunity_id=row["id"],
        reason_code="expensive",
        company_name="Lost Co",
        memory_dir=opp.memory_dir,
    )
    review = svc.dashboard()["weekly_review"]
    assert review["top_rejection_ru"] == "Дорого"
    assert "250" in review["recommendation_ru"]


def test_morning_brief_yesterday_found(health_ctx):
    opp, svc = health_ctx
    y = datetime.now(timezone.utc) - timedelta(days=1)
    ts = y.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()
    opp.create(
        {
            "source_id": "manual",
            "company_name": "Yesterday Lead",
            "status": "new",
            "found_at": ts,
            "updated_at": ts,
        }
    )
    brief = svc.dashboard()["morning_brief"]
    assert any("вчера" in line["text"].lower() for line in brief["lines_ru"])
