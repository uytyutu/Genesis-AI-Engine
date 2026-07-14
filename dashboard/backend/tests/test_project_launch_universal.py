"""Universal project launch — Cycle 14/15 architecture tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.product_line import (
    SERVICE_AUTOMATION,
    SERVICE_CRM,
    SERVICE_SEO,
    SERVICE_WEBSITE,
    project_awaiting_payment_message,
    project_client_current_step,
    project_order_created_message,
)
from app.integration.project_platform.mode import detect_deliverable_intent
from app.integration.project_platform.service import ProjectPlatformService
from app.execution.workspace import ExecutionWorkspaceStore


def test_detect_deliverable_intent_crm():
    intent = detect_deliverable_intent("Хочу CRM для отдела продаж")
    assert intent is not None
    assert intent["service_id"] == SERVICE_CRM


def test_detect_deliverable_intent_automation_sales():
    intent = detect_deliverable_intent("Хочу автоматизировать отдел продаж")
    assert intent is not None
    assert intent["service_id"] == SERVICE_AUTOMATION


def test_detect_deliverable_intent_seo():
    intent = detect_deliverable_intent("Хочу SEO оптимизацию для сайта")
    assert intent is not None
    assert intent["service_id"] == SERVICE_SEO


def test_project_order_created_message_launch_not_site_specific():
    msg = project_order_created_message(
        SERVICE_WEBSITE,
        launch_mode=True,
        project_name="GreenLine",
    )
    assert "GreenLine" in msg
    assert "зафиксирован" in msg
    assert "сайтом" not in msg.lower()
    assert "начнём работу" not in msg.lower()


def test_project_order_created_message_crm_launch():
    msg = project_order_created_message(
        SERVICE_CRM,
        launch_mode=True,
        project_name="Acme",
    )
    assert "CRM" in msg
    assert "Acme" in msg
    assert "сайтом" not in msg.lower()


def test_project_awaiting_payment_launch_preserves_project():
    msg = project_awaiting_payment_message(launch_mode=True)
    assert "согласовали" in msg
    assert "сайт" not in msg.lower()


def test_project_client_current_step_universal():
    step = project_client_current_step(SERVICE_AUTOMATION, "paid")
    assert "сайт" not in step.lower()
    assert "передач" in step.lower()


def test_universal_journey_for_crm_project(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    ws = ExecutionWorkspaceStore(memory).create(owner_id="visitor-crm", title="CRM")
    mapping = memory / "execution" / "visitor_workspaces.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text('{"visitor-crm": "' + ws.workspace_id + '"}', encoding="utf-8")

    svc = ProjectPlatformService(memory)
    activated = svc.activate_project("visitor-crm", title="CRM для склада", service_id=SERVICE_CRM)
    assert activated["has_project"] is True
    journey = activated["project"].get("journey")
    assert journey is not None
    assert any(i["id"] == "type" and i["value"] == "CRM" for i in journey["items"])
    assert any(i["id"] == "launch" for i in journey["items"])


def test_sales_order_launch_message_with_visitor(tmp_path: Path):
    from app.integration.sales_order_service import SalesOrderService

    memory = tmp_path / "memory"
    memory.mkdir()
    ws = ExecutionWorkspaceStore(memory).create(owner_id="visitor-order", title="GreenLine")
    mapping = memory / "execution" / "visitor_workspaces.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text('{"visitor-order": "' + ws.workspace_id + '"}', encoding="utf-8")

    svc_pp = ProjectPlatformService(memory)
    svc_pp.activate_project("visitor-order", title="GreenLine", service_id=SERVICE_WEBSITE)
    svc_pp.record_execution(
        visitor_id="visitor-order",
        workspace_id=ws.workspace_id,
        capability_id="generate_site",
        outputs={"files": ["index.html"], "artifact_id": "a1"},
        goal="Компания GreenLine — солнечные панели",
    )

    class _Factory:
        def submit(self, intent):
            return {"product_id": "p1"}

    sales = SalesOrderService(memory, _Factory())
    out = sales.create_order(
        {
            "business_name": "GreenLine",
            "description": "Солнечные панели для домов",
            "email": "test@example.com",
            "visitor_id": "visitor-order",
            "package_id": "business",
        }
    )
    assert "GreenLine" in out["message"]
    assert "зафиксирован" in out["message"]
    assert "сайтом" not in out["message"].lower()
    assert out["deliverables"][0].startswith("Передача согласованной версии")

    status = sales.public_status(out["order_id"])
    assert "сайт" not in status["current_step"].lower()
    assert status["launch_mode"] is True
