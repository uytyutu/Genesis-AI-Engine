"""Unified farm program bundle."""

from pathlib import Path

from app.integration.farm_program import build_farm_program
from app.integration.first_euro_gate import build_first_euro_gate


def test_farm_program_bundle(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={"connected": True, "submitted_count": 1, "last_run_status": "succeeded"},
        farm_state={"total_tasks_done": 3, "workers_target": 10},
    )
    program = build_farm_program(
        vre_gate=gate,
        finance_guard={"forecast": {"expected_gross_revenue_eur": 0.5}, "revenue_confidence": {"confidence_pct": 38}},
        commercial_evidence=None,
        toloka_status={"submitted_count": 1},
        farm_state={"total_tasks_done": 3, "workers_target": 10},
        labels_export_count=2,
    )
    assert program["program_id"] == "mission1_verified_revenue"
    assert program["vre_level"] == gate["vre_level"]
    assert program["pr_gate"]["active"] is True
    assert len(program["pipeline"]["stages"]) == 8
    assert program["post_first_revenue_questions_ru"]
    assert "force_vectors" in program
    assert "truth_engine" in program
    assert "revenue_path_map" in program
