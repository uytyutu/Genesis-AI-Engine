"""Verified Revenue Engine (VRE) and exchange circuit breaker tests."""

from pathlib import Path

from app.integration.first_euro_gate import build_first_euro_gate, save_ceo_flag
from app.integration.swarm_bridge import ensure_swarm_importable


def test_exchange_breaker_opens_after_threshold(tmp_path: Path):
    ensure_swarm_importable()
    from swarm.exchange_circuit_breaker import ExchangeCircuitBreaker

    mem = tmp_path / "memory"
    mem.mkdir()
    br = ExchangeCircuitBreaker(mem, exchange_id="toloka", failure_threshold=3, open_seconds=60)
    assert not br.safe_mode()
    br.record_failure(error="HTTP 403", http_status=403)
    br.record_failure(error="HTTP 403", http_status=403)
    assert not br.safe_mode()
    opened = br.record_failure(error="HTTP 403", http_status=403)
    assert opened is True
    assert br.safe_mode()
    br.record_success()
    assert not br.safe_mode()


def test_first_euro_gate_blocked_without_work(tmp_path: Path):
    mem = tmp_path / "memory"
    mem.mkdir()
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={"connected": False, "submitted_count": 0, "pending_count": 0},
        farm_state={"total_tasks_done": 0},
    )
    assert gate["verdict"] == "BLOCKED"
    assert gate["vre_level"] == 0
    assert gate["verified_revenue_confirmed"] is False


def test_vre_level_1_pipeline_success(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    export = mem / "swarm_labels_export.jsonl"
    export.write_text('{"task_id":"a1","labels":{}}\n', encoding="utf-8")
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={
            "connected": True,
            "submitted_count": 5,
            "pending_count": 0,
            "last_run_id": "run-1",
            "last_run_status": "succeeded",
            "message": "ok",
        },
        farm_state={"total_tasks_done": 10},
        pipeline_success_count=1,
    )
    assert gate["vre_level"] == 1
    assert gate["verdict"] in {"COMMERCIAL_GATE", "IN_PROGRESS"}


def test_vre_level_4_requires_repeat(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    save_ceo_flag(mem, "wallet_toloka", done=True)
    save_ceo_flag(mem, "withdraw_path", done=True)
    save_ceo_flag(mem, "vre_cycle_repeat", done=True)
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={
            "connected": True,
            "submitted_count": 10,
            "pending_count": 0,
            "last_run_status": "succeeded",
        },
        farm_state={"total_tasks_done": 20},
        pipeline_success_count=3,
    )
    assert gate["vre_level"] == 4
    assert gate["verdict"] == "PASS"
    assert gate["verified_revenue_confirmed"] is True
    assert gate["mission1_freeze"]["pr_gate_question_ru"] == "Помогает получить VRE LEVEL ↑?"


def test_vre_auto_level_4_without_ceo_repeat_flag(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    save_ceo_flag(mem, "wallet_toloka", done=True)
    save_ceo_flag(mem, "withdraw_path", done=True)
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={
            "connected": True,
            "submitted_count": 10,
            "last_run_status": "succeeded",
        },
        farm_state={"total_tasks_done": 20},
        pipeline_success_count=3,
    )
    assert gate["vre_level"] == 4
    assert gate["verdict"] == "PASS"


def test_revenue_confidence_in_gate(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    monkeypatch.setenv("TOLOKA_EXPECTED_PAY_EUR", "0.05")
    gate = build_first_euro_gate(
        memory_dir=mem,
        toloka_status={"connected": True, "submitted_count": 2, "last_run_status": "succeeded"},
        farm_state={"total_tasks_done": 5},
    )
    rc = gate.get("revenue_confidence") or {}
    assert "confidence_pct" in rc
    assert 0 <= rc["confidence_pct"] <= 100
