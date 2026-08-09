"""Bounty queue ≠ API Farm queue; EXECUTION_FAILED not masked as Impossible."""

from __future__ import annotations

from pathlib import Path

import pytest

from swarm.farm_queues import (
    API_FARM_QUEUE,
    BOUNTY_EXECUTION_QUEUE,
    REVENUE_FARM_QUEUE,
    build_farm_queues_status,
)
from swarm.opire_farm import OpireFarmEngine


def test_queue_ids_separated() -> None:
    status = build_farm_queues_status(None)
    assert BOUNTY_EXECUTION_QUEUE in status["queues"]
    assert API_FARM_QUEUE in status["queues"]
    assert REVENUE_FARM_QUEUE in status["queues"]
    assert status["api_farm"]["independent_of_bounty"] is True
    assert status["bounty"]["independent_of_api_farm"] is True


def test_mark_execution_failed_keeps_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FARM_BOUNTY_ADVANCE_ON_FAIL", "0")
    eng = OpireFarmEngine(tmp_path)
    task = {
        "id": "opire:coverage-empty",
        "title": "Improve error when configured code coverage file list is empty",
        "status": "executing",
        "execution_attempts": 1,
        "execution": {"stage": "implementation"},
    }
    failed = eng._mark_execution_failed(
        task,
        detail="patch not obtained: empty coverage file list handler",
        reason="execution_failed",
        stage="implementation",
    )
    assert failed["status"] == "execution_failed"
    assert "Impossible" not in str(failed.get("ceo_note") or "")
    assert failed["execution_error"]
    assert failed["execution"]["stage"] == "implementation"
    assert failed.get("auto_retry_execution") is True
    assert failed.get("error_class")
    assert failed.get("next_action")
    assert failed.get("failure", {}).get("queue") == "BOUNTY_EXECUTION_QUEUE"


def test_api_farm_worker_name() -> None:
    st = build_farm_queues_status(None)
    assert "rapidapi.worker" in st["api_farm"]["worker"]
    assert "OpireFarm" in st["bounty"]["worker"] or "farm_autonomous" in st["bounty"]["worker"]
