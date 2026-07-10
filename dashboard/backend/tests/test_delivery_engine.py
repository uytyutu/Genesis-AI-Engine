"""Delivery Engine — universal service lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.execution.workspace import ExecutionWorkspaceStore
from app.integration.delivery_engine.engine import DeliveryEngine
from app.integration.delivery_engine.gate import delivery_engine_enabled
from app.integration.delivery_engine.phases import (
    STAGE_CONCEPT,
    STAGE_PRELIMINARY_ESTIMATE,
    STAGE_PURCHASE,
    STAGE_REVISION,
    infer_delivery_stage,
)
from app.integration.delivery_engine.service_registry import service_for_capability
from app.integration.product_line import LIFECYCLE_COLLABORATION, SERVICE_WEBSITE


def test_delivery_engine_disabled_by_default(tmp_path: Path):
    assert delivery_engine_enabled(tmp_path) is False


def test_infer_delivery_stage_revision():
    stage = infer_delivery_stage(
        product_phase=LIFECYCLE_COLLABORATION,
        mode="project",
        has_versions=True,
    )
    assert stage == STAGE_REVISION


def test_service_for_capability_universal():
    assert service_for_capability("generate_site") == SERVICE_WEBSITE
    assert service_for_capability("analyze_business_document") == "document_analysis"
    assert service_for_capability("filesystem_write", goal="бизнес-план для кафе") == "business_plan"


def test_execution_complete_advances_delivery(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    ws = ExecutionWorkspaceStore(memory).create(owner_id="v1", title="Test")
    mapping = memory / "execution" / "visitor_workspaces.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text('{"v1": "' + ws.workspace_id + '"}', encoding="utf-8")

    engine = DeliveryEngine(memory)
    out = engine.on_execution_complete(
        visitor_id="v1",
        workspace_id=ws.workspace_id,
        capability_id="generate_site",
        outputs={"files": ["index.html"]},
        goal="Сайт для кафе в Берлине",
        preview_href="/preview",
        primary_label="Открыть",
    )
    assert out["provider"] == "execution"
    assert "version" in out["answer"].lower() or "верси" in out["answer"].lower()
    state = engine.get_public_state("v1")
    assert state["stage"] in (STAGE_CONCEPT, STAGE_REVISION)
    assert state["service"]["service_id"] == SERVICE_WEBSITE


def test_approval_flow_to_purchase(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    ws = ExecutionWorkspaceStore(memory).create(owner_id="v2", title="Site")
    mapping = memory / "execution" / "visitor_workspaces.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text('{"v2": "' + ws.workspace_id + '"}', encoding="utf-8")

    engine = DeliveryEngine(memory)
    engine.on_execution_complete(
        visitor_id="v2",
        workspace_id=ws.workspace_id,
        capability_id="generate_site",
        outputs={"files": ["index.html"]},
        goal="Сайт для стоматологии в Берлине",
    )
    handled = engine.try_handle_message("v2", "Да, всё согласовано — оформляем")
    assert handled is not None
    assert handled.get("cta_href", "").startswith("/order")
    state = engine.get_public_state("v2")
    assert state["stage"] in (STAGE_PRELIMINARY_ESTIMATE, STAGE_PURCHASE)


def test_purchase_type_subscription(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    engine = DeliveryEngine(memory)
    state = engine._store.ensure("v3")
    state.version_count = 1
    state.service_id = SERVICE_WEBSITE
    state.stage = STAGE_PURCHASE
    engine._store.save(state)
    handled = engine.try_handle_message("v3", "Хочу подписку")
    assert handled is not None
    assert handled.get("cta_href", "").startswith("/order")
