"""Unified Vector pipeline — Journey-first intelligence, natural project birth."""

from __future__ import annotations

from app.integration.vector_intelligence.pipeline import analyze_turn
from app.integration.vector_intelligence.project_birth import project_birth_hint


def _biz_history(n: int) -> list[dict[str, str]]:
    msgs: list[dict[str, str]] = []
    for i in range(n):
        msgs.append(
            {"role": "user", "content": f"Хочу открыть ресторан — деталь концепции {i + 1}"}
        )
        msgs.append({"role": "assistant", "content": f"Ответ {i + 1}"})
    return msgs


def test_casual_question_is_open_dialog_not_project_work():
    a = analyze_turn("Как дела?")
    assert a.journey_phase == "open_dialog"
    assert a.need == "companion"
    assert a.action == "answer_naturally"
    assert a.is_casual_turn is True
    assert "без продаж" in a.priority or "консультации" in a.priority


def test_dinner_question_open_dialog():
    a = analyze_turn("Что приготовить на ужин?")
    assert a.journey_phase == "open_dialog"
    assert a.need in ("companion", "expert")
    assert a.intent in ("free_talk", "learn")
    assert not a.project_birth_ready


def test_space_question_open_dialog():
    a = analyze_turn("Расскажи про космос")
    assert a.journey_phase in ("open_dialog",)
    assert a.need in ("companion", "expert")
    assert a.action == "answer_naturally"


def test_restaurant_idea_accepts_responsibility_not_advisor():
    a = analyze_turn("Хочу открыть ресторан")
    assert a.journey_phase == "accept_responsibility"
    assert a.intent in ("explore_idea", "build_result", "continue_work")
    assert a.need == "helper"
    assert a.action == "explore_together"
    assert a.project_birth_ready is False


def test_project_birth_after_deep_business_thread():
    history = _biz_history(8)
    a = analyze_turn(
        "Давай зафиксируем концепцию",
        history=history,
    )
    assert a.project_birth_ready is True
    assert a.journey_phase == "requirements"
    assert a.action == "suggest_save_project"
    hint = project_birth_hint(a)
    assert hint and "сохранить" in hint.lower()


def test_active_project_uses_journey_phase_on_work_topic():
    from app.integration.vector_intelligence.client_life_context import ClientLifeContext

    life = ClientLifeContext(
        visitor_id="v1",
        has_project=True,
        project_title="Сайт кафе",
        next_step_hint="посмотреть версию 1",
        progress_percent=65,
        version_count=1,
    )
    a = analyze_turn("Что дальше по сайту?", life=life)
    assert a.journey_phase in ("show_progress", "creation", "understand_goal")
    assert a.action == "manage_project"


def test_casual_overrides_project_context():
    from app.integration.vector_intelligence.client_life_context import ClientLifeContext

    life = ClientLifeContext(visitor_id="v1", has_project=True, project_title="Сайт")
    a = analyze_turn("Почему небо голубое?", life=life)
    assert a.is_casual_turn is True
    assert a.journey_phase == "open_dialog"
    assert a.need == "companion"


def test_mandate_emphasizes_journey_not_role_ladder():
    a = analyze_turn("Как дела?")
    block = a.to_mandate_block()
    assert "Project Execution Journey" in block
    assert "Journey:" in block
    assert "Собеседник" not in block
    assert "Memory" in block
    assert "Context" in block
    assert "Planner" in block
    assert "tier" not in block.lower()
    assert "groq" not in block.lower()


def test_workforce_channel_internal_only():
    a = analyze_turn("Помоги написать договор на немецком")
    assert a.workforce_channel == "deep_reasoning"
    assert a.to_mandate_block().count("tier") == 0
