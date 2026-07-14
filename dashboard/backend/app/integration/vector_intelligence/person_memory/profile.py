"""Planner-facing person understanding — selective recall, not full dump."""

from __future__ import annotations

from app.integration.vector_intelligence.person_memory.schema import PersonProfile
from app.integration.vector_intelligence.pipeline import VectorTurnPlan
from app.integration.vector_intelligence.types import JourneyPhase

_OPEN_DIALOG = frozenset({"open_dialog"})
_SURFACE_ON_CONTINUE = frozenset(
    {"goals", "projects", "preferences", "decisions", "budget", "agreements"}
)
_SURFACE_EARLY_JOURNEY = frozenset({"goals", "projects", "preferences", "budget"})
_DO_NOT_SURFACE_CASUAL = frozenset(
    {"goals", "projects", "budget", "decisions", "agreements", "preferences"}
)
_ACTIVE_JOURNEY = frozenset(
    {
        "show_progress",
        "revisions",
        "ready",
        "verification",
        "gate",
        "launch",
        "creation",
        "materials",
        "requirements",
    }
)


def do_not_surface(turn: VectorTurnPlan) -> frozenset[str]:
    """What Planner should not mention this turn."""
    if turn.is_casual_turn or turn.journey_phase in _OPEN_DIALOG:
        return _DO_NOT_SURFACE_CASUAL
    if turn.journey_phase == "open_dialog":
        return frozenset({"budget", "agreements", "decisions"})
    return frozenset()


def categories_for_turn(turn: VectorTurnPlan) -> frozenset[str]:
    blocked = do_not_surface(turn)
    if turn.journey_phase in _ACTIVE_JOURNEY or turn.intent == "continue_work":
        allowed = _SURFACE_ON_CONTINUE
    elif turn.journey_phase in ("accept_responsibility", "understand_goal"):
        allowed = _SURFACE_EARLY_JOURNEY
    else:
        return frozenset()
    return allowed - blocked


def build_planner_memory_block(
    profile: PersonProfile,
    turn: VectorTurnPlan,
) -> str:
    """
    Selective understanding for Planner — Memory serves Personality, not the reverse.
    Empty block is valid (silence is sometimes best memory).
    """
    cats = categories_for_turn(turn)
    if not cats and not (
        profile.active_path.summary
        and turn.intent in ("continue_work", "explore_idea")
        and not turn.is_casual_turn
    ):
        return (
            "## Understanding (Person Memory)\n"
            "- На этот ход долгий контекст не нужен — ответьте по сути вопроса.\n"
            "- Не упоминайте прошлые проекты и бюджет без запроса."
        )

    lines = [
        "## Understanding (Person Memory)",
        "Память — вход для Planner, не инструкция. Выводы делаете вы. "
        "Не цитируйте даты и сообщения. При confidence < 0.7 — лучше уточнить.",
    ]
    blocked = do_not_surface(turn)

    if profile.active_path.summary and "projects" not in blocked:
        ap = profile.active_path
        if cats or turn.intent == "continue_work" or turn.action == "manage_project":
            lines.append(f"- Активный путь: {ap.summary} (этап: {ap.stage})")
            if ap.confidence < 0.7:
                lines.append("- Путь: уверенность средняя — можно мягко уточнить")

    for atom in profile.active_atoms():
        if atom.category not in cats:
            continue
        if atom.confidence < 0.5:
            continue
        prefix = ""
        if atom.status == "stale":
            prefix = "[устарело — уточнить] "
        elif atom.confidence < 0.7:
            prefix = "[уточнить] "
        lines.append(f"- {prefix}{atom.display}")

    if len(lines) == 2:
        lines.append("- Пока мало устойчивого контекста — слушайте и запоминайте естественно.")

    silent = do_not_surface(turn)
    if silent:
        labels = ", ".join(sorted(silent))
        lines.append(f"- Не поднимать сейчас: {labels}")

    return "\n".join(lines)
