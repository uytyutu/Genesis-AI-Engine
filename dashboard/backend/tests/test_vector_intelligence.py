"""Vector Intelligence Layer — initiative and client life context."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.execution.workspace import ExecutionWorkspaceStore
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer
from app.integration.genesis_brain.public_brand import PUBLIC_WELCOME
from app.integration.product_line import LIFECYCLE_HANDOFF
from app.integration.project_platform.service import ProjectPlatformService, resolve_workspace_id
from app.integration.project_platform.store import ProjectStore
from app.integration.vector_intelligence.client_life_context import build_client_life_context
from app.integration.vector_intelligence.initiative import (
    build_action_first_hint,
    build_proactive_greeting,
    touch_last_seen,
)
from app.integration.vector_intelligence.service import VectorIntelligenceService


def _seed_memory(memory: Path, visitor_id: str, *, days_ago: float, visit_count: int = 3) -> None:
    layer = GenesisMemoryLayer(memory)
    now = datetime.now(timezone.utc)
    last_seen = now - timedelta(days=days_ago)
    layer.save(
        visitor_id,
        {
            "visitor_id": visitor_id,
            "name": "Анна",
            "facts": [{"text": "Владелец кофейни в Германии"}],
            "visit_count": visit_count,
            "last_seen_at": last_seen.isoformat(),
        },
    )


def _record_site_version(memory: Path, visitor_id: str) -> None:
    ws_id = resolve_workspace_id(memory, visitor_id)
    if not ws_id:
        ws = ExecutionWorkspaceStore(memory).create(owner_id=visitor_id, title="Test")
        mapping = memory / "execution" / "visitor_workspaces.json"
        mapping.parent.mkdir(parents=True, exist_ok=True)
        mapping.write_text(f'{{"{visitor_id}": "{ws.workspace_id}"}}', encoding="utf-8")
        ws_id = ws.workspace_id
    ProjectPlatformService(memory).record_execution(
        visitor_id=visitor_id,
        workspace_id=ws_id,
        capability_id="generate_site",
        outputs={"files": ["index.html"], "artifact_id": "a1"},
        goal="сайт для кафе",
    )


def test_first_visit_uses_public_welcome(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    ctx = build_client_life_context("visitor-new", memory_dir=memory)
    assert ctx.visit_count == 0
    assert build_proactive_greeting(ctx) == PUBLIC_WELCOME


def test_return_after_two_days_continues_project(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "visitor-return"
    _seed_memory(memory, vid, days_ago=3)
    ProjectPlatformService(memory).activate_project(
        vid,
        title="Сайт кофейни",
        service_id="website",
    )

    greeting = VectorIntelligenceService(memory).proactive_greeting(vid)
    assert "Добро пожаловать обратно" in greeting
    assert "Сайт кофейни" in greeting or "остановились" in greeting
    assert "продолжить" in greeting.lower()


def test_inactive_week_prompts_resume(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "visitor-inactive"
    _seed_memory(memory, vid, days_ago=8)
    ProjectPlatformService(memory).activate_project(vid, title="CRM для кафе", service_id="crm")

    greeting = build_proactive_greeting(build_client_life_context(vid, memory_dir=memory))
    assert "Давно не было активности" in greeting
    assert "CRM для кафе" in greeting
    assert "Хотите продолжить" in greeting


def test_first_version_ready_offers_review(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "visitor-version"
    layer = GenesisMemoryLayer(memory)
    layer.save(vid, {"visitor_id": vid, "name": "Иван", "visit_count": 4})
    ProjectPlatformService(memory).activate_project(vid, title="Лендинг", service_id="website")
    _record_site_version(memory, vid)

    ctx = build_client_life_context(vid, memory_dir=memory)
    assert ctx.first_version_ready is True
    greeting = build_proactive_greeting(ctx)
    assert "черновик" in greeting.lower()
    assert "доработать" in greeting.lower()


def test_journey_suggests_next_logical_step(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "visitor-journey"
    layer = GenesisMemoryLayer(memory)
    layer.save(
        vid,
        {
            "visitor_id": vid,
            "name": "Мария",
            "facts": [{"text": "кофейня в Берлине"}],
            "visit_count": 6,
        },
    )
    ProjectPlatformService(memory).activate_project(vid, title="Сайт кофейни", service_id="website")
    _record_site_version(memory, vid)
    ws_id = resolve_workspace_id(memory, vid)
    assert ws_id
    record = ProjectStore(memory).load(ws_id)
    assert record
    record.lifecycle_phase = LIFECYCLE_HANDOFF
    ProjectStore(memory).save(record)

    ctx = build_client_life_context(vid, memory_dir=memory)
    assert ctx.progress_percent >= 70
    assert ctx.next_logical_label
    greeting = build_proactive_greeting(ctx)
    assert "почти закончили" in greeting.lower() or "логично" in greeting.lower()


def test_action_first_hint_includes_life_context_and_mandate(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "visitor-hint"
    _seed_memory(memory, vid, days_ago=10)
    ProjectPlatformService(memory).activate_project(vid, title="Сайт", service_id="website")

    hint = build_action_first_hint(
        build_client_life_context(vid, memory_dir=memory),
        user_message="что дальше?",
    )
    assert "КОНТЕКСТ ЖИЗНИ КЛИЕНТА" in hint
    assert "ДЕЙСТВИЕ ПЕРВИЧНО" in hint
    assert "Какое одно действие" in hint
    assert "вернуть в работу" in hint or "следующ" in hint.lower()


def test_touch_last_seen_updates_memory(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    vid = "visitor-touch"
    layer = GenesisMemoryLayer(memory)
    data = layer.load(vid)
    assert "last_seen_at" not in data

    touch_last_seen(data)
    layer.save(vid, data)
    reloaded = layer.load(vid)
    assert reloaded.get("last_seen_at")
