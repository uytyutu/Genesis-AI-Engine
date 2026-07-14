"""Project Platform — project-centric customer layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.project_platform.mode import detect_deliverable_intent
from app.integration.project_platform.service import ProjectPlatformService
from app.execution.workspace import ExecutionWorkspaceStore


def test_detect_deliverable_intent_site():
    intent = detect_deliverable_intent("Хочу сайт для стоматологии в Берлине")
    assert intent is not None
    assert intent["service_id"] == "website"


def test_detect_deliverable_intent_casual_none():
    assert detect_deliverable_intent("Привет, как дела?") is None


def test_project_activate_and_record(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    ws = ExecutionWorkspaceStore(memory).create(owner_id="visitor-1", title="Test")
    mapping = memory / "execution" / "visitor_workspaces.json"
    mapping.parent.mkdir(parents=True, exist_ok=True)
    mapping.write_text('{"visitor-1": "' + ws.workspace_id + '"}', encoding="utf-8")

    svc = ProjectPlatformService(memory)
    activated = svc.activate_project("visitor-1", title="Сайт кафе", service_id="website")
    assert activated["has_project"] is True
    assert activated["project"]["title"] == "Сайт кафе"

    svc.record_execution(
        visitor_id="visitor-1",
        workspace_id=ws.workspace_id,
        capability_id="generate_site",
        outputs={"files": ["index.html"], "artifact_id": "a1"},
        goal="сайт для кафе",
    )
    state = svc.get_for_visitor("visitor-1")
    assert state["has_project"] is True
    assert len(state["project"]["versions"]) == 1
    assert state["project"]["versions"][0]["label"] == "Версия 1"
    assert len(state["project"]["timeline"]) >= 2
    assert state["project"]["identity"]["type_label"] == "Сайт для бизнеса"
    assert state["project"]["progress"]["percent"] >= 28
    assert isinstance(state["project"]["artifact_folders"], list)
    assert any(f["id"] == "website" for f in state["project"]["artifact_folders"])
    assert state["project"]["health"]["emoji"]
    assert state["project"]["next_action"]["label"]
    assert state["project"]["activity"]["summary"]


def test_bootstrap_from_message_creates_project(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = ProjectPlatformService(memory)
    state = svc.bootstrap_from_message("visitor-pe1", "Хочу создать сайт для компании")
    assert state["has_project"] is True
    assert state["project"]["mode"] == "project"
    assert state["project"]["service_id"] == "website"


def test_empty_visitor_state(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    state = ProjectPlatformService(memory).get_for_visitor("new-visitor")
    assert state["has_project"] is False
    assert state["mode"] == "conversation"
