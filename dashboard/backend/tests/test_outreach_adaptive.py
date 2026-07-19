"""Adaptive Outreach Intelligence — per-country scale/protect."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.outreach_adaptive_service import OutreachAdaptiveService


@pytest.fixture(autouse=True)
def _pacing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_OUTREACH_MIN_INTERVAL_SEC", "0")


def _rows_for(code: str, *, sent: int, replies: int, orders: int = 0) -> list[dict]:
    rows = []
    for i in range(sent):
        status = "contacted"
        outreach = "sent"
        interactions = []
        revenue = 0
        if i < replies:
            status = "replied"
            outreach = "replied"
            interactions = [{"event": "replied"}]
        if i < orders:
            status = "won"
            revenue = 350
        rows.append(
            {
                "market": code,
                "meta": {"market": code},
                "status": status,
                "outreach_status": outreach,
                "interactions": interactions,
                "revenue_eur": revenue,
            }
        )
    return rows


def test_scale_up_excellent_market(tmp_path: Path):
    svc = OutreachAdaptiveService(tmp_path)
    # 20 sent, 5 replies (~25% reply) → excellent → scale up from base DE 20
    rows = _rows_for("DE", sent=20, replies=5, orders=1)
    result = svc.run_weekly_review(rows, force=True, apply=True)
    assert result["ok"] and not result.get("skipped")
    de = next(d for d in result["decisions"] if d["code"] == "DE")
    assert de["decision"] == "scale_up"
    assert de["to_cap"] > de["from_cap"]
    assert svc.effective_daily_cap("DE") == de["to_cap"]


def test_scale_down_on_bounce(tmp_path: Path):
    svc = OutreachAdaptiveService(tmp_path)
    # Seed override high, then bounce storm
    state = svc._load_state()
    state["cap_overrides"] = {"US": 60}
    svc._save_state(state)
    rows = []
    for i in range(20):
        rows.append(
            {
                "market": "US",
                "meta": {"market": "US", "email_bounced": True},
                "status": "contacted",
                "outreach_status": "bounced",
                "interactions": [],
                "revenue_eur": 0,
            }
        )
    result = svc.run_weekly_review(rows, force=True, apply=True)
    us = next(d for d in result["decisions"] if d["code"] == "US")
    assert us["decision"] == "scale_down"
    assert us["to_cap"] < 60
    assert "bounce" in us["reason"] or us["health"]["label"] == "Poor"


def test_countries_independent(tmp_path: Path):
    svc = OutreachAdaptiveService(tmp_path)
    rows = _rows_for("DE", sent=20, replies=6, orders=2) + [
        {
            "market": "US",
            "meta": {"market": "US", "email_bounced": True},
            "status": "contacted",
            "outreach_status": "bounced",
            "interactions": [],
            "revenue_eur": 0,
        }
        for _ in range(20)
    ]
    result = svc.run_weekly_review(rows, force=True, apply=True)
    by = {d["code"]: d for d in result["decisions"]}
    assert by["DE"]["decision"] == "scale_up"
    assert by["US"]["decision"] == "scale_down"


def test_profit_hold_without_revenue(tmp_path: Path):
    svc = OutreachAdaptiveService(tmp_path)
    # Excellent replies but €0 → HOLD (no scale_up)
    rows = _rows_for("DE", sent=20, replies=5, orders=0)
    health = svc.health_score(svc.collect_market_metrics(rows)["DE"])
    assert health["can_scale_up"] is False
    assert "replies_without_revenue" in health["reasons"] or "no_revenue_hold" in health["reasons"]
    result = svc.run_weekly_review(rows, force=True, apply=True)
    de = next(d for d in result["decisions"] if d["code"] == "DE")
    assert de["decision"] in ("hold", "pause", "scale_down")
    assert de["decision"] != "scale_up"


def test_dashboard_roi_and_shared(tmp_path: Path):
    svc = OutreachAdaptiveService(tmp_path)
    rows = _rows_for("DE", sent=10, replies=2, orders=1)
    dash = svc.dashboard(rows)
    assert dash["ok"]
    assert dash.get("shared_global") is False
    assert "roi_table" in dash
    de_roi = next(r for r in dash["roi_table"] if r["code"] == "DE")
    assert de_roi["orders"] == 1
    assert de_roi["spent_eur"] > 0
