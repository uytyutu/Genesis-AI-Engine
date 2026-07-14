"""Person Memory v1 — trust, selective recall, Planner-facing blocks."""

from __future__ import annotations

import tempfile
from pathlib import Path

from app.integration.vector_intelligence.client_life_context import ClientLifeContext
from app.integration.vector_intelligence.person_memory.extract import should_persist
from app.integration.vector_intelligence.person_memory.profile import (
    build_planner_memory_block,
    do_not_surface,
)
from app.integration.vector_intelligence.person_memory.service import PersonMemoryService
from app.integration.vector_intelligence.pipeline import analyze_turn


def _svc(tmp: Path) -> PersonMemoryService:
    return PersonMemoryService(tmp)


def test_budget_supersedes_40k_to_60k():
    with tempfile.TemporaryDirectory() as td:
        svc = _svc(Path(td))
        vid = "ceo-test"
        svc.observe_turn(vid, "Хочу открыть кофейню в Берлине")
        svc.observe_turn(vid, "Бюджет около 40 000 €")
        svc.observe_turn(vid, "Бюджет 60 000 €")

        profile = svc.load(vid)
        budget_atoms = [a for a in profile.atoms if a.category == "budget"]
        active = [a for a in budget_atoms if a.status not in ("obsolete", "forgotten", "archived")]
        assert len(active) == 1
        assert "60" in active[0].display
        obsolete = [a for a in budget_atoms if a.status == "obsolete"]
        assert len(obsolete) == 1
        assert "40" in obsolete[0].display


def test_casual_turn_does_not_persist():
    with tempfile.TemporaryDirectory() as td:
        svc = _svc(Path(td))
        vid = "casual"
        turn = analyze_turn("Как дела?")
        assert turn.is_casual_turn is True
        assert should_persist("Как дела?", turn=turn) is False

        svc.observe_turn(vid, "Как дела?", turn=turn)
        profile = svc.load(vid)
        assert not profile.atoms
        assert not profile.active_path.summary


def test_continue_without_project_uses_active_path():
    life = ClientLifeContext(
        visitor_id="v1",
        has_project=False,
        active_path_summary="открывает кофейню (Berlin)",
    )
    a = analyze_turn("Ну что, продолжаем?", life=life)
    assert a.journey_phase == "accept_responsibility"
    assert a.intent == "continue_work"
    assert "кофейн" in a.priority.lower() or "открывает" in a.priority.lower()


def test_planner_block_hides_context_on_companion():
    with tempfile.TemporaryDirectory() as td:
        svc = _svc(Path(td))
        vid = "hide"
        svc.observe_turn(vid, "Хочу открыть кофейню в Берлине")
        svc.observe_turn(vid, "Бюджет 40 000 €")

        turn = analyze_turn("Как дела?")
        block = svc.planner_block(vid, turn)
        assert "Не упоминайте" in block or "не нужен" in block
        assert do_not_surface(turn)  # non-empty

        profile = svc.load(vid)
        companion_block = build_planner_memory_block(profile, turn)
        assert "бюджет" not in companion_block.lower() or "не упоминайте" in companion_block.lower()


def test_active_path_in_greeting_context():
    with tempfile.TemporaryDirectory() as td:
        memory_dir = Path(td)
        vid = "greet"
        svc = _svc(memory_dir)
        svc.observe_turn(vid, "Хочу открыть кофейню в Берлине")

        from app.integration.vector_intelligence.client_life_context import build_client_life_context

        ctx = build_client_life_context(vid, memory_dir=memory_dir)
        assert ctx.active_path_summary
        assert "кофейн" in ctx.active_path_summary.lower() or "Berlin" in ctx.active_path_summary
