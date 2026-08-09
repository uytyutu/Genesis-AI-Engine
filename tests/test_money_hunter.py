"""Money Hunter P0 — import, profit, approval, reality separation."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.money_hunter.profit import compute_economics, opportunity_score
from swarm.money_hunter.service import MoneyHunterService
from swarm.money_hunter.toloka_provider import TolokaProvider


@pytest.fixture()
def mh(tmp_path: Path) -> MoneyHunterService:
    return MoneyHunterService(tmp_path)


def test_import_and_score(mh: MoneyHunterService) -> None:
    res = mh.import_opportunity(
        {
            "source": "manual",
            "title": "German Business Research — public company facts",
            "description": "Research 20 German SMEs: website, phone, category. CSV deliverable.",
            "url": "https://example.com/job/1",
            "budget_min": 100,
            "budget_max": 150,
            "currency": "EUR",
        }
    )
    assert res["ok"] is True
    opp = res["opportunity"]
    assert opp["id"].startswith("mh-")
    assert opp["status"] in ("PENDING_APPROVAL", "QUALIFIED", "REJECTED")
    eco = opp["economics"]
    assert eco["expected_revenue"] > 0
    assert "expected_profit" in eco
    assert eco["human_summary"]["opportunity_score"].endswith("/100")


def test_dedupe(mh: MoneyHunterService) -> None:
    payload = {
        "source": "upwork_manual",
        "title": "Data cleaning CSV",
        "description": "Clean and verify CSV rows",
        "url": "https://example.com/job/dup",
        "budget_min": 80,
        "budget_max": 80,
        "currency": "EUR",
    }
    a = mh.import_opportunity(payload)
    b = mh.import_opportunity(payload)
    assert a["ok"] and b["ok"]
    assert b["deduped"] is True
    assert a["opportunity"]["id"] == b["opportunity"]["id"]


def test_rejection_forbidden(mh: MoneyHunterService) -> None:
    res = mh.import_opportunity(
        {
            "source": "manual",
            "title": "Need captcha bypass farm",
            "description": "Build captcha bypass and fake engagement spam",
            "budget_min": 200,
            "budget_max": 200,
            "currency": "EUR",
        }
    )
    assert res["opportunity"]["status"] == "REJECTED"
    assert res["opportunity"]["economics"]["decision"] == "REJECT"


def test_approval_gate(mh: MoneyHunterService) -> None:
    res = mh.import_opportunity(
        {
            "source": "manual",
            "title": "Market research DE cleaning niche",
            "description": "Public web research competitors and prices. CSV + short report.",
            "budget_min": 120,
            "budget_max": 120,
            "currency": "EUR",
        }
    )
    oid = res["opportunity"]["id"]
    preview = mh.approve(oid, confirm=False)
    assert preview["requires_confirm"] is True
    assert "approval_preview" in preview

    blocked = mh.start_execution(oid)
    assert blocked["ok"] is False

    done = mh.approve(oid, confirm=True, note="CEO ok")
    assert done["ok"] is True
    assert done["opportunity"]["status"] == "APPROVED"
    assert done["proposal"]["auto_submit"] is False

    started = mh.start_execution(oid)
    assert started["ok"] is True
    assert started["opportunity"]["status"] == "EXECUTING"


def test_potential_not_revenue(mh: MoneyHunterService) -> None:
    mh.import_opportunity(
        {
            "source": "manual",
            "title": "Competitor research",
            "description": "Research public competitor sites",
            "budget_min": 90,
            "budget_max": 90,
            "currency": "EUR",
        }
    )
    reality = mh.reality()
    assert reality["real_revenue_eur"] == 0
    assert reality["pipeline_value_eur"] > 0
    assert reality["real_paid_orders"] == 0


def test_settlement_hard_real(mh: MoneyHunterService) -> None:
    res = mh.import_opportunity(
        {
            "source": "manual",
            "title": "Data verification batch",
            "description": "Verify structured public data fields",
            "budget_min": 60,
            "budget_max": 60,
            "currency": "EUR",
        }
    )
    oid = res["opportunity"]["id"]
    mh.approve(oid, confirm=True)
    bad = mh.record_settlement(oid, {"amount": 60, "currency": "EUR"})
    assert bad["ok"] is False
    assert bad.get("potential_only") is True

    good = mh.record_settlement(
        oid,
        {
            "external_payout_id": "paypal_txn_test_1",
            "amount": 60,
            "currency": "EUR",
            "paid_at": "2026-08-09T10:00:00+00:00",
            "source_id": "paypal",
        },
    )
    assert good["ok"] is True
    assert good["real_revenue_eur"] == 60
    dup = mh.record_settlement(
        oid,
        {
            "external_payout_id": "paypal_txn_test_1",
            "amount": 60,
            "currency": "EUR",
            "paid_at": "2026-08-09T10:00:00+00:00",
            "source_id": "paypal",
        },
    )
    assert dup.get("duplicate") is True
    reality = mh.reality()
    assert reality["real_revenue_eur"] == 60
    assert reality["real_paid_orders"] == 1


def test_toloka_no_auto_create() -> None:
    p = TolokaProvider()
    est = p.estimate_cost(hours=2)
    assert est["estimated_cost_eur"] > 0
    assert est["is_revenue"] is False
    created = p.create_task(approved=False)
    assert created["ok"] is False


def test_profit_math() -> None:
    eco = compute_economics(
        {
            "source": "upwork_manual",
            "title": "Research",
            "description": "Public market research CSV",
            "budget_min": 100,
            "budget_max": 100,
            "currency": "EUR",
            "estimated_hours": 2,
            "automation_percent": 80,
        }
    )
    assert eco["expected_profit"] == pytest.approx(
        eco["expected_revenue"] - eco["expected_cost"], rel=1e-3
    )
    score = opportunity_score(
        expected_profit=eco["expected_profit"],
        expected_revenue=eco["expected_revenue"],
        success_probability=eco["success_probability"] / 100.0,
        automation_percent=eco["automation_percent"],
        risk_score=eco["risk_score"],
        hours=eco["estimated_hours"],
    )
    assert 0 <= score <= 100
