"""Virtus Core Alpha Hunter / Income Lab — paper first, ≤2% experiments."""

from __future__ import annotations

from pathlib import Path

from datetime import datetime, timezone

import pytest

from swarm.alpha_hunter_v1 import (
    LC_PREPARED,
    LC_WAITING_APPROVAL,
    MAX_EXPERIMENT_PCT,
    STAGE_PAPER,
    STAGE_PROPOSE,
    AlphaHunterLab,
    expected_profit_range,
    experiment_cap_eur,
    micro_test_quote_eur,
    passes_director_threshold,
)
from swarm.income_engine_v1 import IncomeEngineV1


class _Mem:
    def __init__(self, root: Path) -> None:
        self.root = root


def test_experiment_cap_2pct():
    assert experiment_cap_eur(20.0) == pytest.approx(0.40)
    assert MAX_EXPERIMENT_PCT == 0.02
    assert micro_test_quote_eur(20.0) == pytest.approx(0.40)


def test_paper_day_keeps_candidates_under_discovery_threshold(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    out = lab.run_paper_day(bank_eur=20.0, opportunities_target=100)
    assert out["ok"] is True
    brief = out["director_brief"]
    assert brief["kept"] >= 1
    assert out.get("top_strategies")
    assert lab.panel()["lab"]["active_experiments"] == 0


def test_heal_stale_strict_brief(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    state = lab._load_lab()
    state["director"] = {
        "min_expected_profit_eur": 500.0,
        "min_roi_pct": 30.0,
        "thresholds_locked": False,
        "last_brief": {
            "found": 100,
            "rejected": 100,
            "kept": 0,
            "message_ru": (
                "Анализ: нашёл 100 возможностей. 100 отклонил "
                "(порог €500 / ROI 30%). Ни одной выше порога — мелочь не показываю."
            ),
        },
    }
    lab._save_lab(state)
    panel = lab.panel()
    assert panel["director"]["min_expected_profit_eur"] == pytest.approx(50.0)
    assert panel["director"]["search_mode"] == "newbie"
    assert panel["director"]["last_brief"] is None
    assert panel["next_step"] == "adapters"
    assert "адаптер" in panel["next_action_ru"].lower() or "Adapter" in panel["next_action_ru"] or "адаптеры" in panel["next_action_ru"].lower()


def test_search_modes_and_honest_empty_conservative(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    assert lab.set_search_mode("conservative")["ok"] is True
    out = lab.run_paper_day(bank_eur=20.0, opportunities_target=100)
    brief = out["director_brief"]
    assert "rejection_breakdown" in brief
    assert brief.get("coverage", {}).get("sources_checked", 0) >= 1
    # Conservative may keep 0 — that must be empty_ok, not an error
    if brief["kept"] == 0:
        assert brief.get("empty_ok") is True
        assert "нормальный результат" in brief["message_ru"].lower() or "критериям" in brief["message_ru"]
        soft = lab.set_search_mode("explorer")
        assert soft["ok"] is True
        again = lab.run_paper_day(bank_eur=20.0, opportunities_target=100)
        assert again["director_brief"]["kept"] >= 1


def test_adaptive_suggestion_after_100_experiments(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    lab.set_search_mode("newbie")
    state = lab._load_lab()
    state["lifetime"] = {
        "experiments": 100,
        "success": 40,
        "failed": 60,
        "avg_realized_roi": 0.15,
    }
    lab._save_lab(state)
    sug = lab.adaptive_threshold_suggestion(lab._load_lab())
    assert sug["ready"] is True
    assert sug.get("suggest_mode") == "balanced"


def test_heal_stuck_active_experiments(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    state = lab._load_lab()
    state["active_experiments"] = 10
    state["lifetime"] = {"experiments": 0}
    state["today"] = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "spent_eur": 0,
        "returned_eur": 0,
        "paper_modeled": 0,
    }
    lab._save_lab(state)
    lab.panel()
    assert lab._load_lab()["active_experiments"] == 0


def test_propose_after_adapter_cycle(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    out = lab.run_adapter_execution_cycle(bank_eur=20.0)
    assert out["hits_count"] >= 1
    prop = lab.propose_top(bank_eur=20.0, n=3)
    assert prop["ok"] is True
    assert prop.get("found") is True
    assert prop["proposals"][0]["executable_action"]["id"]
    assert prop["proposals"][0]["test_cost_eur"] == 0.0
    assert lab._load_lab()["stage"] == STAGE_PROPOSE


def test_propose_rejects_synthetic_paper(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    lab.run_paper_day(bank_eur=20.0, opportunities_target=40)
    prop = lab.propose_top(bank_eur=20.0, n=3)
    assert prop["ok"] is True
    assert prop.get("found") is False
    assert "NO_OPPORTUNITY" in prop["message_ru"] or "адаптер" in prop["message_ru"].lower()


def test_approve_blocked_in_paper_stage(tmp_path: Path):
    eng = IncomeEngineV1(_Mem(tmp_path), swarm_size=40)
    out = eng.start_mission(balance_eur=20.0)
    mission = out["mission"]
    mission["scan_complete_ts"] = 0
    mission["ends_ts"] = 0
    state = eng._load_state()
    mission = eng._tick_mission(state, mission)
    state["mission"] = mission
    eng._save_state(state)
    if not mission.get("opportunities"):
        pytest.skip("no opps")
    bad = eng.approve(mission["opportunities"][0]["id"], mode="once")
    assert bad["ok"] is False
    assert bad["error"] == "stage_paper"


def test_approve_after_propose_stage(tmp_path: Path):
    eng = IncomeEngineV1(_Mem(tmp_path), swarm_size=40)
    eng.set_stage(STAGE_PROPOSE)
    # Income-engine swarm approve still works in propose; Alpha micro-test needs LIVE
    out = eng.start_mission(balance_eur=20.0)
    mission = out["mission"]
    mission["scan_complete_ts"] = 0
    mission["ends_ts"] = 0
    state = eng._load_state()
    mission = eng._tick_mission(state, mission)
    state["mission"] = mission
    eng._save_state(state)
    if not mission.get("opportunities"):
        pytest.skip("no opps")
    oid = mission["opportunities"][0]["id"]
    res = eng.approve(oid, mode="once")
    assert res["ok"] is True
    assert res["executed"][0]["execution"]["profit_recorded_eur"] == 0.0
    assert res["executed"][0]["execution"]["search_spend_eur"] == 0.0


def test_evidence_and_profit_range_not_single_number(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    out = lab.run_paper_day(bank_eur=20.0, opportunities_target=40)
    assert out["ok"] is True
    opps = out.get("opportunities") or lab.list_opportunities(limit=10)
    assert opps
    o = opps[0]
    assert o.get("evidence", {}).get("source")
    assert o.get("evidence", {}).get("reasons")
    assert o.get("lifecycle") in (
        "DISCOVERED",
        "VERIFIED",
        "PREPARED",
        LC_PREPARED,
    )
    profit = o.get("expected_profit") or {}
    assert "low_eur" in profit and "high_eur" in profit
    assert "worst_case_eur" in profit and "best_case_eur" in profit
    rng = expected_profit_range(modeled_roi=0.4, family="new_market")
    assert rng["display_ru"].startswith("€")
    assert "–" in rng["display_ru"] or "-" in rng["display_ru"]


def test_propose_requires_analysis_then_waiting_approval(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    bad = lab.propose_top(bank_eur=20.0)
    assert bad.get("ok") is False
    lab.run_adapter_execution_cycle(bank_eur=20.0)
    prop = lab.propose_top(bank_eur=20.0, n=3)
    assert prop.get("ok") is True
    assert prop.get("found") is True
    p0 = prop["proposals"][0]
    assert p0.get("executable_action", {}).get("id")
    assert p0.get("lifecycle") == LC_WAITING_APPROVAL


def test_director_hides_penny_deals():
    assert not passes_director_threshold(
        expected_profit_eur=2.0,
        modeled_roi=0.05,
        min_profit_eur=500.0,
        min_roi_pct=30.0,
    )
    assert passes_director_threshold(
        expected_profit_eur=2800.0,
        modeled_roi=0.11,
        min_profit_eur=500.0,
        min_roi_pct=30.0,
    )
    assert passes_director_threshold(
        expected_profit_eur=40.0,
        modeled_roi=0.35,
        min_profit_eur=500.0,
        min_roi_pct=30.0,
    )


def test_propose_filters_below_threshold(tmp_path: Path):
    """Paper-only strategies never enter Approve — regardless of forced ROI."""
    lab = AlphaHunterLab(_Mem(tmp_path))
    lab.set_director_thresholds(min_expected_profit_eur=500.0, min_roi_pct=30.0)
    lab.run_paper_day(bank_eur=20.0, opportunities_target=80)
    strategies = lab._load_strategies()
    for s in strategies.get("items") or []:
        s["modeled_roi"] = 0.05
        s["expected_profit_eur"] = 2.0
    lab._save_strategies(strategies)
    prop = lab.propose_top(bank_eur=20.0, n=3)
    assert prop["found"] is False
    assert prop["director_brief"]["kept"] == 0


def test_payout_desk_no_invented_balance(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    bad = lab.request_withdraw(confirm=True)
    assert bad["ok"] is False
    lab.record_experiment_result(
        spent_eur=0.4, returned_eur=1.2, success=True, strategy_id="s1"
    )
    panel = lab.panel()
    assert panel["payout"]["available_eur"] == pytest.approx(0.8)
    out = lab.request_withdraw(confirm=True)
    assert out["ok"] is True
    assert out["withdrawn_eur"] == pytest.approx(0.8)


def test_approve_micro_test_dry_run_no_invented_profit(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    lab.run_adapter_execution_cycle(bank_eur=20.0)
    prop = lab.propose_top(bank_eur=20.0, n=1)
    assert prop.get("found") is True
    sid = prop["proposals"][0]["strategy_id"]
    blocked = lab.approve_micro_test(sid, bank_eur=20.0)
    assert blocked["ok"] is False
    assert blocked["error"] == "not_live"
    live = lab.go_live()
    assert live["ok"] is True
    out = lab.approve_micro_test(sid, bank_eur=20.0)
    assert out["ok"] is True
    assert out["experiment"]["search_spend_eur"] == 0.0
    assert out["experiment"]["profit_recorded_eur"] == 0.0
    assert out["experiment"]["test_cost_eur"] == 0.0
    assert out["experiment"]["executable_action"]["id"]
    assert out["lab"]["lab"]["active_experiments"] >= 1
    arts = out["experiment"].get("artifacts") or {}
    assert arts.get("draft_md") or arts.get("draft_json")


def test_scan_intervals_and_go_live_gate(tmp_path: Path):
    lab = AlphaHunterLab(_Mem(tmp_path))
    assert lab.go_live()["ok"] is False
    bad = lab.set_scan_interval(999)
    assert bad["ok"] is False
    ok = lab.set_scan_interval(120)
    assert ok["ok"] is True
    assert ok["scan_interval_sec"] == 120
    lab.run_paper_day(bank_eur=20.0, opportunities_target=20)
    assert lab._load_lab()["analysis_ready"] is True
    assert lab._load_lab()["lab_mode"] == "analysis"
    assert lab.go_live()["ok"] is True
    assert lab._load_lab()["lab_mode"] == "live"
