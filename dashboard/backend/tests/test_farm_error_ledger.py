"""Error Ledger, Truth Engine, Explainability tests."""

from pathlib import Path

from app.integration.farm_program import build_farm_program, build_revenue_path_map
from app.integration.first_euro_gate import build_first_euro_gate
from app.integration.swarm_bridge import ensure_swarm_importable


def test_classify_format_error():
    ensure_swarm_importable()
    from swarm.farm_error_ledger import classify_error

    assert classify_error(message="invalid json schema for field task_id") == "format"
    assert classify_error(message="HTTP 403 forbidden", http_status=403) == "api"


def test_error_ledger_append_and_summary(tmp_path: Path):
    ensure_swarm_importable()
    from swarm.farm_error_ledger import FarmErrorLedger

    mem = tmp_path / "memory"
    mem.mkdir()
    ledger = FarmErrorLedger(mem)
    ledger.append(
        exchange="toloka",
        stage="add_dataset_items",
        message="required field missing",
        http_status=400,
        batch_size=5,
        sample_task_ids=["t1"],
    )
    summary = ledger.summary()
    assert summary["total_logged"] == 1
    assert summary["by_taxonomy"].get("format") == 1 or summary["by_taxonomy"].get("data") == 1


def test_truth_engine_estimates_gross_not_fact(tmp_path: Path, monkeypatch):
    ensure_swarm_importable()
    from swarm.truth_engine import build_truth_sheet

    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    sheet = build_truth_sheet(
        toloka_status={"connected": True, "submitted_count": 2, "last_run_status": "succeeded"},
        vre_gate={"vre_level": 1, "revenue_confidence": {"confidence_pct": 38}},
        finance_guard={"forecast": {"expected_gross_revenue_eur": 0.82}},
        ceo_flags={},
    )
    kinds = {r["key"]: r["truth_kind"] for r in sheet["records"]}
    assert kinds["expected_gross_revenue"] == "ESTIMATE"
    assert kinds["pipeline_finished"] == "FACT"
    assert kinds["toloka_will_pay"] == "HYPOTHESIS"


def test_explainability_channel_review():
    ensure_swarm_importable()
    from swarm.farm_explainability import explain_vre_verdict

    exp = explain_vre_verdict(
        verdict="CHANNEL_REVIEW",
        vre_gate={
            "channel_review_required": True,
            "vre_level": 1,
            "revenue_confidence": {"confidence_pct": 94},
            "ceo_action_now": "Сменить канал",
        },
        toloka_status={"pipeline_success_count": 3},
    )
    assert exp["probabilities"]["monetization_model"] == "высокая"
    assert exp["probabilities"]["code_bug"] == "низкая"


def test_revenue_path_map_blocker_at_wallet(tmp_path: Path):
    stages = [{"id": "submit", "done": True}, {"id": "export", "done": True}]
    m = build_revenue_path_map(vre_level=1, pipeline_stages=stages, ceo_flags={})
    assert "wallet" in (m["blocker_ru"] or "").lower() or "Pipeline" in (m["blocker_ru"] or "")
    assert m["current_step_ru"]


def test_farm_program_includes_force_vectors_and_truth(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={"connected": True, "submitted_count": 1, "last_run_status": "succeeded"},
        farm_state={"total_tasks_done": 3},
        pipeline_success_count=1,
    )
    program = build_farm_program(
        vre_gate=gate,
        finance_guard={"forecast": {"expected_gross_revenue_eur": 0.5}},
        commercial_evidence=None,
        toloka_status={"submitted_count": 1, "last_run_status": "succeeded"},
        farm_state={"total_tasks_done": 3, "workers_target": 10},
        labels_export_count=2,
        ceo_flags={},
        error_ledger_summary={"total_logged": 0},
    )
    assert program["force_vectors"]["vectors"]
    assert program["truth_engine"]["records"]
    assert program["revenue_path_map"]["steps"]
    assert program["explainability"]["title_ru"]
