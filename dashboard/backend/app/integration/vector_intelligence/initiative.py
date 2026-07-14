"""Vector initiative — proactive employee, not passive chat."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, PUBLIC_WELCOME
from app.integration.vector_intelligence.client_life_context import ClientLifeContext
from app.integration.vector_intelligence.pipeline import VectorTurnPlan, analyze_turn
from app.integration.vector_intelligence.project_birth import project_birth_hint


def _greeting_name(ctx: ClientLifeContext) -> str:
    if ctx.name:
        return f", {ctx.name}"
    return ""


def build_proactive_greeting(ctx: ClientLifeContext) -> str:
    """Opening when user returns — employee remembers context."""
    if ctx.visit_count <= 1 and not ctx.has_project:
        return PUBLIC_WELCOME

    if ctx.is_inactive_week and ctx.has_project and ctx.project_title:
        return (
            f"Добро пожаловать обратно{ _greeting_name(ctx)}.\n\n"
            f"Давно не было активности по проекту «{ctx.project_title}».\n"
            f"Последний раз мы остановились на этапе: {ctx.last_stop_summary or 'работе над результатом'}.\n\n"
            "Хотите продолжить?"
        )

    if ctx.is_return_after_days:
        if ctx.active_path_summary:
            return (
                f"Добро пожаловать обратно{ _greeting_name(ctx)}.\n\n"
                f"Последний раз мы остановились на: {ctx.active_path_summary}.\n\n"
                "Хотите продолжить с этого места?"
            )
        if ctx.has_project:
            stop = ctx.last_stop_summary or ctx.stage_label or "предыдущем этапе"
            return (
                f"Добро пожаловать обратно{ _greeting_name(ctx)}.\n\n"
                f"Последний раз мы остановились на: {stop}.\n\n"
                "Хотите продолжить с этого места?"
            )
        return (
            f"Добро пожаловать обратно{ _greeting_name(ctx)}.\n\n"
            "Рад новой встрече. Продолжим с того, что важно, или начнём новую тему?"
        )

    if ctx.first_version_ready and ctx.project_title:
        return (
            f"С возвращением{ _greeting_name(ctx)}.\n\n"
            f"По «{ctx.project_title}» есть черновик — могу показать или доработать по вашей просьбе."
        )

    if ctx.business_label and ctx.journey_services:
        journey = " → ".join(ctx.journey_services[:3])
        if ctx.next_logical_label and ctx.progress_percent >= 70:
            return (
                f"С возвращением{ _greeting_name(ctx)}.\n\n"
                f"Мы почти закончили текущий этап ({ctx.stage_label or 'работа'}).\n"
                f"После него логично {ctx.next_logical_label}.\n\n"
                "Продолжим?"
            )
        return (
            f"Рад снова видеть{ _greeting_name(ctx)}.\n\n"
            f"Помню ваш путь: {journey}.\n"
            "О чём поговорим сегодня — продолжим или новая задача?"
        )

    return (
        f"Здравствуйте{ _greeting_name(ctx)}! Я {ASSISTANT_NAME}.\n\n"
        "Можем поговорить о чём угодно — или заняться вашим делом, когда будете готовы."
    )


def build_action_first_hint(
    ctx: ClientLifeContext,
    *,
    user_message: str = "",
    history: list[dict[str, str]] | None = None,
    has_attachments: bool = False,
    analysis: VectorTurnPlan | None = None,
    memory_dir: Path | None = None,
) -> str:
    """
    Internal mandate before each reply:
    «Какое действие сейчас больше всего поможет этому человеку?»
    """
    turn = analysis or analyze_turn(
        user_message,
        history=history,
        life=ctx,
        has_attachments=has_attachments,
    )
    birth = project_birth_hint(turn)
    parts: list[str] = []
    if memory_dir:
        from app.integration.vector_intelligence.person_memory.service import PersonMemoryService

        parts.append(PersonMemoryService(memory_dir).planner_block(ctx.visitor_id, turn))
    else:
        parts.append(ctx.to_prompt_block())
    parts.extend(["", turn.to_mandate_block()])
    if birth:
        parts.extend(["", birth])
    return "\n".join(parts)


def touch_last_seen(memory_data: dict, *, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    memory_data["last_seen_at"] = now.isoformat()
    return memory_data
