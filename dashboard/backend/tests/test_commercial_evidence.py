"""Commercial evidence + finance guard tests."""

from pathlib import Path

from app.integration.commercial_evidence import build_commercial_evidence, save_evidence
from app.integration.swarm_bridge import ensure_swarm_importable


def test_commercial_evidence_tech_ok_commercial_unknown(tmp_path: Path):
    mem = tmp_path / "memory"
    mem.mkdir()
    (mem / "swarm_labels_export.jsonl").write_text('{"task_id":"1","labels":{}}\n', encoding="utf-8")
    report = build_commercial_evidence(
        memory_dir=mem,
        farm_state={"total_tasks_done": 5},
        toloka_status={
            "submitted_count": 3,
            "pending_count": 0,
            "last_run_id": "r1",
            "last_run_status": "succeeded",
            "dataset_id": "ds-1",
            "auto_submit_enabled": True,
        },
        ceo_flags={},
        last_tick={"tasks_done": 2, "earned_eur": 0.1, "llm_cost_eur": 0.02},
        spider_meta={"scanned": 10, "passed_gate": 4},
    )
    assert report["verdict_code"] == "TECH_OK_COMMERCIAL_UNKNOWN"
    assert "requester" in report["toloka_model_note_ru"].lower() or "Pipeline" in report["toloka_model_note_ru"]
    assert len(report["rows"]) >= 7
    save_evidence(mem, report)
    assert (mem / "commercial_evidence_latest.json").is_file()


def test_finance_guard_negative_streak(tmp_path: Path, monkeypatch):
    ensure_swarm_importable()
    from swarm.finance_guard import FinanceGuard

    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_FINANCE_GUARD_STOP", "1")
    monkeypatch.setenv("TOLOKA_EXPECTED_PAY_EUR", "0.01")
    g = FinanceGuard(mem)
    for _ in range(3):
        r = g.evaluate_tick(earned_eur=0.01, llm_cost_eur=0.05, tasks_done=1)
    assert r["stop_farm"] is True
    assert r["negative_streak"] >= 3


def test_finance_guard_daily_forecast_roi():
    ensure_swarm_importable()
    from swarm.finance_guard import FinanceGuard

    g = FinanceGuard(Path("/tmp/unused-fg"))
    f = g.daily_forecast(
        farm_state={"today_earned_eur": 0.62, "llm_cost_eur": 0.18, "total_tasks_done": 12},
        pending_submit=0,
    )
    assert f["spend_eur"] == 0.18
    assert f["expected_income_eur"] == 0.62
    assert f["roi_pct"] is not None


def test_finance_guard_forecast_with_expected_pay(tmp_path: Path, monkeypatch):
    ensure_swarm_importable()
    from swarm.finance_guard import FinanceGuard

    monkeypatch.setenv("TOLOKA_EXPECTED_PAY_EUR", "0.05")
    mem = tmp_path / "memory"
    mem.mkdir()
    g = FinanceGuard(mem)
    f = g.daily_forecast(
        farm_state={"today_earned_eur": 0.1, "llm_cost_eur": 0.18, "total_tasks_done": 10},
        pending_submit=4,
    )
    assert f["expected_income_eur"] >= 0.5
    assert f["roi_pct"] is not None


def test_vre_channel_review_verdict(tmp_path: Path, monkeypatch):
    from app.integration.first_euro_gate import build_first_euro_gate

    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={
            "connected": True,
            "submitted_count": 10,
            "pending_count": 0,
            "last_run_status": "succeeded",
            "message": "ok",
        },
        farm_state={"total_tasks_done": 5},
        pipeline_success_count=3,
    )
    assert gate["verdict"] == "CHANNEL_REVIEW"
    assert gate["channel_review_required"] is True
