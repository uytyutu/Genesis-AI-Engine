"""Toloka auto-submit — export jsonl → Pipeline dataset."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.integration.business_mode_service import BusinessModeService
from app.integration.finance_service import FinanceService
from app.integration.micro_farm_service import MicroFarmService
from app.integration.opportunity_service import OpportunityService
from app.integration.swarm_bridge import ensure_swarm_importable


@pytest.fixture
def farm_memory(tmp_path: Path) -> Path:
    mem = tmp_path / "memory"
    mem.mkdir()
    return mem


def _make_farm(memory: Path) -> MicroFarmService:
    opp = OpportunityService(memory)
    return MicroFarmService(
        opp,
        FinanceService(memory),
        business_mode=BusinessModeService(memory),
        memory_dir=memory,
    )


def test_toloka_submitter_pending_and_state(farm_memory: Path, monkeypatch):
    ensure_swarm_importable()
    from swarm.toloka_submit import TolokaLabelSubmitter

    export = farm_memory / "swarm_labels_export.jsonl"
    export.write_text(
        json.dumps(
            {
                "task_id": "t1",
                "source_id": "asset_scan",
                "labels": {"niche_tags": ["retail"]},
                "exported_at": "2026-07-14T12:00:00+00:00",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("FARM_LIVE_MODE", "live")
    monkeypatch.setenv("TOLOKA_AUTO_SUBMIT", "1")

    adapter = MagicMock()
    adapter.configured.return_value = True
    adapter.check_connection.return_value = {"connected": True, "message": "ok"}
    adapter.list_projects.return_value = {
        "ok": True,
        "projects": [{"id": "proj-1", "status": "active"}],
    }
    adapter.list_project_datasets.return_value = {"ok": True, "datasets": []}
    adapter.create_dataset.return_value = {
        "ok": True,
        "dataset": {"id": "ds-1", "name": "virtus-core-labels"},
    }
    adapter.add_dataset_items.return_value = {"ok": True, "http_status": 200}
    adapter.list_project_pipelines.return_value = {
        "ok": True,
        "pipelines": [{"id": "pipe-1"}],
    }
    adapter.attach_pipeline_dataset.return_value = {"ok": True}
    adapter.start_pipeline_run.return_value = {"ok": True, "run": {"id": "run-1"}}

    submitter = TolokaLabelSubmitter(memory_dir=farm_memory, adapter=adapter)
    assert submitter.status()["pending_count"] == 1

    result = submitter.submit_pending(limit=10)
    assert result["ok"] is True
    assert result["submitted"] == 1
    assert submitter.status()["pending_count"] == 0
    adapter.add_dataset_items.assert_called_once()
    call_kw = adapter.add_dataset_items.call_args.kwargs
    assert call_kw["items"][0]["task_id"] == "t1"
    assert "retail" in call_kw["items"][0]["labels_json"]


def test_micro_farm_submit_toloka_logs_journal(farm_memory: Path):
    farm = _make_farm(farm_memory)
    export = farm_memory / "swarm_labels_export.jsonl"
    export.write_text(
        json.dumps({"task_id": "x2", "labels": {"sentiment": "neutral"}}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    fake_result = {
        "ok": True,
        "submitted": 1,
        "message": "Toloka приняла 1 разметок",
        "dataset_id": "ds-abc",
    }

    with patch.object(farm, "_toloka_submitter") as mock_sub:
        mock_sub.return_value.submit_pending.return_value = fake_result
        out = farm.submit_toloka_labels(limit=5)

    assert out["submitted"] == 1
    events = farm._recent_events(5)
    assert any(e.get("title_ru") == "Пакет отправлен на Toloka" for e in events)


def test_toloka_adapter_add_dataset_items_posts_items():
    ensure_swarm_importable()
    from swarm.adapter_toloka import TolokaAdapter

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"{}"
    mock_response.json.return_value = {}

    with patch("swarm.adapter_toloka.httpx.Client") as mock_client:
        mock_client.return_value.__enter__.return_value.post.return_value = mock_response
        result = TolokaAdapter(api_key="tok").add_dataset_items(
            "ds-99",
            items=[{"task_id": "a", "labels_json": "{}"}],
            fields=[{"name": "task_id"}],
        )

    assert result["ok"] is True
    post_call = mock_client.return_value.__enter__.return_value.post.call_args
    assert "/datasets/ds-99/items" in post_call[0][0]
