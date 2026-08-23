"""API Farm RapidAPI channel — scoring, lifecycle, durable jobs, revenue gates."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from swarm.farm_channels.rapidapi import builder, publisher, quality_gate, research, revenue, scoring, worker
from swarm.farm_channels.rapidapi.models import (
    REV_EARNED,
    REV_PAID_OUT,
    STATUS_APPROVAL_REQUIRED,
    STATUS_QUALITY_GATE_FAILED,
)
from swarm.farm_channels.rapidapi.store import ApiFarmStore


@pytest.fixture()
def store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ApiFarmStore:
    monkeypatch.delenv("RAPIDAPI_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_PROVIDER_KEY", raising=False)
    monkeypatch.delenv("RAPIDAPI_PUBLISH_TOKEN", raising=False)
    monkeypatch.setenv("GENESIS_API_PUBLIC_URL", "https://api.virtuscore.test")
    return ApiFarmStore(tmp_path)


def test_scoring_penalizes_missing_evidence(store: ApiFarmStore) -> None:
    low = scoring.score_candidate(
        {
            "name": "Vague API",
            "demand_score": 70,
            "competition_score": 40,
            "implementation_score": 70,
            "monetization_score": 70,
            "evidence": [],
            "suggested_price": {"PRO": 25},
            "operating_cost": 1.0,
        }
    )
    high = scoring.score_candidate(
        {
            "name": "OCR Invoice API",
            "demand_score": 70,
            "competition_score": 40,
            "implementation_score": 70,
            "monetization_score": 70,
            "evidence": [{"type": "hypothesis", "note": "signal"}],
            "suggested_price": {"PRO": 25},
            "operating_cost": 1.0,
        }
    )
    assert low["total_score"] < high["total_score"]
    assert low["evidence_penalty_applied"] is True
    assert high["evidence_penalty_applied"] is False


def test_discover_dedupes_candidates(store: ApiFarmStore) -> None:
    first = research.discover_candidates(store, limit=20)
    assert first
    n1 = len(store.list_candidates())
    second = research.discover_candidates(store, limit=20)
    n2 = len(store.list_candidates())
    assert n2 == n1
    assert second == []


def test_lifecycle_to_approval_or_gate(store: ApiFarmStore) -> None:
    worker.enqueue_pipeline(store, discover=True)
    for _ in range(40):
        out = worker.step(store)
        if out.get("idle"):
            break
    statuses = {c.get("status") for c in store.list_candidates()}
    assert statuses & {
        STATUS_APPROVAL_REQUIRED,
        STATUS_QUALITY_GATE_FAILED,
        "CANDIDATE",
        "BUILDING",
        "TESTING",
        "QUALITY_GATE",
        "READY",
    }
    assert any(c.get("total_score", 0) > 0 for c in store.list_candidates())


def test_quality_gate_fail_without_pricing(store: ApiFarmStore) -> None:
    row = store.upsert_candidate(
        {
            "id": "cand_bad_price",
            "name": "Broken Pricing API",
            "problem": "test",
            "upstream": "none",
            "expected_margin": 1.0,
            "operating_cost": 0.1,
            "publish_package": {
                "plan": {
                    "openapi": {"openapi": "3.0.3", "paths": {"/x": {}}},
                    "readme": "# hi",
                    "pricing": {},
                    "validation": True,
                    "timeout_sec": 10,
                    "rate_limit": {"rpm": 60},
                    "tests_planned": ["unit"],
                    "upstream": "none",
                },
                "artifacts_dir": str(store.memory_dir / "missing"),
            },
        }
    )
    result = quality_gate.run_quality_gate(store, row["id"])
    assert result["ok"] is False
    failed = result["quality_gate"]["failed"]
    assert "pricing_valid" in failed or failed
    assert store.get_candidate(row["id"])["status"] == STATUS_QUALITY_GATE_FAILED


def test_approval_blocks_publish(store: ApiFarmStore) -> None:
    built = builder.build_candidate(
        store,
        store.upsert_candidate(
            {
                "id": "cand_no_approve",
                "name": "Need Approval",
                "problem": "CEO gate test",
                "category": "Test",
                "endpoints": [{"method": "GET", "path": "/health"}],
                "upstream": "none",
                "suggested_price": {"BASIC": 0, "PRO": 19, "ULTRA": 49, "MEGA": 99},
                "operating_cost": 0.5,
                "evidence": [{"type": "test"}],
            }
        )["id"],
    )
    assert built.get("ok") is True
    cid = "cand_no_approve"
    quality_gate.run_quality_gate(store, cid)
    out = publisher.publish_candidate(store, cid)
    assert out.get("ok") is False
    assert out.get("requires_ceo_action") is True
    assert out.get("error") == "approval_required"


def test_durable_job_survives_reload(tmp_path: Path) -> None:
    s1 = ApiFarmStore(tmp_path)
    research.discover_candidates(s1, limit=1)
    s1.enqueue_job("discover")
    assert (tmp_path / "api_farm_candidates.json").is_file()
    assert (tmp_path / "api_farm_jobs.jsonl").is_file()
    s2 = ApiFarmStore(tmp_path)
    assert len(s2.list_candidates()) >= 1
    assert len(s2.list_jobs(limit=50)) >= 1
    data = json.loads((tmp_path / "api_farm_candidates.json").read_text(encoding="utf-8"))
    assert data.get("candidates")


def test_revenue_idempotent_and_paid_out_only_to_ledger(
    store: ApiFarmStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger_calls: list[dict] = []

    def _fake_append(event: dict, *, memory_dir):
        ledger_calls.append(event)
        return "ledger-uuid-1"

    monkeypatch.setattr(revenue, "_try_append_ledger", _fake_append)

    evt = {
        "external_id": "rap_pay_1",
        "status": REV_PAID_OUT,
        "amount": 12.5,
        "currency": "USD",
        "settled_at": "2026-08-08T12:00:00Z",
        "payout_id": "pp_1",
        "candidate_id": "cand_x",
    }
    r1 = revenue.ingest_revenue_event(store, evt)
    r2 = revenue.ingest_revenue_event(store, evt)
    assert r1.get("ok") is True
    assert r1.get("actual_revenue_increased") is True
    assert r2.get("duplicate") is True
    assert len(ledger_calls) == 1
    assert ledger_calls[0].get("provider") == "rapidapi" or ledger_calls[0].get("external_id")

    earned = revenue.ingest_revenue_event(
        store,
        {
            "external_id": "rap_earn_1",
            "status": REV_EARNED,
            "amount": 3.0,
            "currency": "USD",
            "candidate_id": "cand_x",
        },
    )
    assert earned.get("ok") is True
    assert earned.get("actual_revenue_increased") is False
    assert len(ledger_calls) == 1


def test_auto_publish_always_false() -> None:
    assert publisher.auto_publish_allowed() is False


def test_money_monitor_exposes_api_farm_and_hero() -> None:
    import sys

    backend_root = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from app.integration.money_monitor_service import build_money_monitor

    payload = build_money_monitor(farm_state={"total_earned_eur": 99.0, "total_tasks_done": 0})
    assert "api_farm" in payload
    hero = payload["real_revenue_hero"]
    assert "total_actual_eur" in hero
    assert float(hero["farm_potential_not_real_eur"]) >= 0
    assert hero["training_ledger_not_real_eur"] == 99.0
    # Training must not inflate total_actual by itself
    assert float(hero["total_actual_eur"]) == float(hero["stripe_gross_eur"]) + float(
        hero["api_farm_eur"]
    )
