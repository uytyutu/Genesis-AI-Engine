"""Unified Vector intelligence — Journey-first pipeline (not a model router)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.integration.genesis_brain.layers.conversation_type import (
    ConversationKind,
    classify_conversation_type,
    is_business_mode,
    is_product_mode,
)
from app.integration.genesis_brain.workforce_performance import WorkforceTask
from app.integration.vector_intelligence.client_life_context import ClientLifeContext
from app.integration.vector_intelligence.planner import PlannerDecision, plan_for_human
from app.integration.vector_intelligence.types import (
    VECTOR_JOURNEY_OS,
    JOURNEY_PHASE_LABELS,
    JOURNEY_PHASE_PRIORITY,
    JourneyPhase,
    VectorAction,
    VectorIntent,
    VectorNeed,
)
from app.integration.vector_intelligence.workforce_hint import (
    WorkforceChannel,
    WorkforceTier,
    channel_to_task,
    select_workforce_channel,
)

_CASUAL_KINDS = frozenset(
    {
        "casual_conversation",
        "humor",
        "philosophy",
        "science",
        "education",
        "general_question",
        "personal_reflection",
        "creative",
        "meta_correction",
    }
)
_SUPPORT_KINDS = frozenset({"emotional_support"})

_PROJECT_CONTINUE = re.compile(
    r"продолж|дальше|статус|верси|сайт|проект|правк|готово|посмотр|этап|ну что",
    re.I,
)
_BUSINESS_TOPIC = re.compile(
    r"ресторан|кофейн|кафе|бизнес|открыть|магазин|салон|ниша|концепц",
    re.I,
)

_ACTIVE_PROJECT_PHASES = frozenset(
    {
        "show_progress",
        "revisions",
        "ready",
        "verification",
        "gate",
        "launch",
    }
)


def _build_memory_summary(life: ClientLifeContext) -> str:
    lines = ["## Memory (что Vector уже знает о человеке)"]
    if life.name:
        lines.append(f"- Имя: {life.name}")
    if life.business_label:
        lines.append(f"- Бизнес / занятость: {life.business_label}")
    if life.market:
        lines.append(f"- Рынок: {life.market}")
    if life.journey_services:
        lines.append(f"- Путь: {' → '.join(life.journey_services[:4])}")
    if life.interests:
        lines.append(f"- Интересы: {', '.join(life.interests[:4])}")
    if life.days_since_last_seen is not None and life.days_since_last_seen >= 1:
        lines.append(f"- Не виделись: {int(life.days_since_last_seen)} дн.")
    if len(lines) == 1:
        lines.append("- Пока мало личного контекста — слушайте и запоминайте естественно.")
    return "\n".join(lines)


def _build_context_summary(
    life: ClientLifeContext,
    *,
    has_attachments: bool,
    turn_count: int,
) -> str:
    lines = ["## Context (что есть вокруг этого разговора)"]
    if life.has_project and life.project_title:
        lines.append(f"- Активный проект: «{life.project_title}»")
        if life.stage_label:
            lines.append(f"- Этап: {life.stage_label} ({life.progress_percent}%)")
        if life.last_stop_summary:
            lines.append(f"- Где остановились: {life.last_stop_summary}")
        if life.next_step_hint:
            lines.append(f"- Следующий шаг: {life.next_step_hint}")
    elif life.active_path_summary:
        lines.append(f"- Активный путь: {life.active_path_summary}")
        lines.append("- Отдельного проекта пока нет — продолжаем путь к результату.")
    else:
        lines.append("- Отдельного проекта пока нет — это нормально.")
    if has_attachments:
        lines.append("- Есть вложения — можно опереться на документы.")
    if life.version_count:
        lines.append(f"- Версий результата: {life.version_count}")
    lines.append(f"- Сообщений в этой нити: ~{turn_count}")
    return "\n".join(lines)


def _project_phase_from_life(life: ClientLifeContext) -> JourneyPhase:
    stage_low = (life.stage_label or "").lower()
    pct = life.progress_percent

    if "оформлен" in stage_low or "оплат" in stage_low or "запуск" in stage_low:
        return "launch"
    if "gate" in stage_low or "подтвержд" in stage_low:
        return "gate"
    if "провер" in stage_low:
        return "verification"
    if "правк" in stage_low or "изменен" in stage_low:
        return "revisions"
    if "материал" in stage_low:
        return "materials"
    if "требован" in stage_low or "brief" in stage_low or "тз" in stage_low:
        return "requirements"
    if pct >= 95:
        return "gate"
    if pct >= 85 or ("готов" in stage_low and pct >= 70):
        return "ready"
    if pct >= 60:
        return "show_progress"
    if life.version_count >= 1 or pct >= 40:
        return "creation"
    if pct >= 25 or "сбор" in stage_low:
        return "materials"
    if pct >= 10:
        return "requirements"
    return "understand_goal"


def _infer_journey_phase(
    *,
    kind: ConversationKind,
    user_message: str,
    life: ClientLifeContext,
    is_casual: bool,
    project_turn: bool,
    project_birth_ready: bool,
    business_depth: int,
) -> JourneyPhase:
    if is_casual and not project_turn:
        return "open_dialog"

    if project_turn or (
        life.has_project
        and kind in ("business_consulting", "product_creation", "programming")
    ):
        if life.has_project:
            return _project_phase_from_life(life)
        if life.active_path_summary:
            return "accept_responsibility"
        return "understand_goal"

    if project_birth_ready:
        return "requirements"

    if is_product_mode(kind):
        if life.has_project:
            return _project_phase_from_life(life) if life.progress_percent else "creation"
        return "accept_responsibility"

    if is_business_mode(kind) or _BUSINESS_TOPIC.search(user_message):
        if business_depth >= 4:
            return "understand_goal"
        return "accept_responsibility"

    if life.has_project and not is_casual:
        return _project_phase_from_life(life)

    return "open_dialog"


def _compat_routing(
    journey_phase: JourneyPhase,
    *,
    kind: ConversationKind,
    project_birth_ready: bool,
    life: ClientLifeContext,
    is_casual: bool,
) -> tuple[VectorIntent, VectorNeed, VectorAction]:
    """Legacy intent/need/action — workforce routing only, not public behavior."""
    if journey_phase == "open_dialog":
        if kind in ("science", "education"):
            return "learn", "expert", "answer_naturally"
        if is_casual and kind in _SUPPORT_KINDS:
            return "support", "companion", "answer_naturally"
        return "free_talk", "companion", "answer_naturally"

    if journey_phase in _ACTIVE_PROJECT_PHASES:
        return "continue_work", "employee", "manage_project"

    if journey_phase == "requirements" and project_birth_ready:
        return "explore_idea", "helper", "suggest_save_project"

    if journey_phase == "creation":
        return "build_result", "helper", "execute"

    if journey_phase in ("accept_responsibility", "understand_goal", "materials"):
        if life.active_path_summary:
            return "continue_work", "helper", "explore_together"
        if is_product_mode(kind):
            return "build_result", "helper", "execute" if life.has_project else "explore_together"
        return "explore_idea", "helper", "explore_together"

    if journey_phase == "show_progress":
        return "continue_work", "employee", "manage_project"

    if journey_phase == "revisions":
        return "continue_work", "employee", "manage_project"

    return "explore_idea", "helper", "explore_together"


def _priority_for_phase(
    journey_phase: JourneyPhase,
    *,
    life: ClientLifeContext,
    project_birth_ready: bool,
) -> str:
    if journey_phase in _ACTIVE_PROJECT_PHASES and life.next_step_hint:
        return life.next_step_hint
    if journey_phase == "accept_responsibility" and life.active_path_summary:
        return life.active_path_summary
    if project_birth_ready and journey_phase == "requirements":
        return "подвести итог обсуждения и мягко предложить сохранить как проект"
    return JOURNEY_PHASE_PRIORITY[journey_phase]


@dataclass(frozen=True)
class VectorTurnPlan:
    conversation_kind: ConversationKind
    journey_phase: JourneyPhase
    intent: VectorIntent
    need: VectorNeed
    action: VectorAction
    priority: str
    memory_summary: str
    context_summary: str
    planner: PlannerDecision
    workforce_channel: WorkforceChannel
    workforce_task: WorkforceTask
    workforce_tier: WorkforceTier
    project_birth_ready: bool = False
    is_casual_turn: bool = False

    def to_mandate_block(self) -> str:
        lines = [
            VECTOR_JOURNEY_OS,
            "",
            "## Этот ход",
            f"- Journey: {JOURNEY_PHASE_LABELS[self.journey_phase]}",
            f"- Intent (internal): {self.intent}",
            "",
            self.memory_summary,
            "",
            self.context_summary,
            "",
            self.planner.to_block(),
            "",
            "## ДЕЙСТВИЕ ПЕРВИЧНО",
            "Какое одно действие сейчас больше всего продвинет человека на этом этапе Journey?",
            f"**Приоритет:** {self.priority}",
        ]
        if self.project_birth_ready:
            lines.append(
                "- Обсуждение созрело — мягко предложите сохранить как проект (только с согласия)."
            )
        if self.journey_phase == "open_dialog":
            lines.append("- Открытый диалог: без проектов и бизнес-продаж.")
        elif self.journey_phase in _ACTIVE_PROJECT_PHASES:
            lines.append(
                "- Активный проект: сначала движение к результату; на сторонний вопрос — полный ответ."
            )
        lines.append(
            "\nВы — **Vector**. Один человек. Меняется только этап Journey, не личность."
        )
        return "\n".join(lines)


def compact_fast_lane_hint(plan: VectorTurnPlan) -> str:
    """Minimal mandate for fast-lane LLM prefill."""
    lines = [
        "## Этот ход (internal, кратко)",
        f"Journey: {JOURNEY_PHASE_LABELS[plan.journey_phase]}",
        f"Приоритет: {plan.priority}",
        f"Действие: {plan.action}",
    ]
    if plan.journey_phase == "open_dialog":
        lines.append("Открытый диалог — без продаж и проектов.")
    elif plan.journey_phase not in ("open_dialog", "gate", "launch"):
        lines.append(
            "Задача в работе — признайте этап, предложите конкретный следующий шаг. "
            "Без длинного вступления."
        )
    lines.append("Вы — Vector. Один голос. Ответ на языке пользователя.")
    return "\n".join(lines)


VectorTurnAnalysis = VectorTurnPlan


def _count_business_user_turns(messages: list[dict[str, str]] | None) -> int:
    if not messages:
        return 0
    count = 0
    prefix: list[dict[str, str]] = []
    for m in messages:
        if m.get("role") != "user":
            continue
        text = (m.get("content") or "").strip()
        if not text:
            continue
        kind = classify_conversation_type(text, messages=prefix)
        prefix.append(m)
        if kind in ("business_consulting", "product_creation") or _BUSINESS_TOPIC.search(text):
            count += 1
    return count


def analyze_turn(
    user_message: str,
    *,
    history: list[dict[str, str]] | None = None,
    life: ClientLifeContext | None = None,
    has_attachments: bool = False,
    project_birth_min_turns: int = 8,
) -> VectorTurnPlan:
    """Journey-first pipeline for one turn."""
    life = life or ClientLifeContext(visitor_id="anonymous")
    messages = list(history or [])
    if user_message.strip():
        messages = messages + [{"role": "user", "content": user_message.strip()}]

    kind = classify_conversation_type(user_message, messages=messages[:-1] if messages else None)
    business_depth = _count_business_user_turns(messages)
    turn_count = sum(1 for m in messages if m.get("role") == "user")

    project_birth_ready = (
        not life.has_project
        and business_depth >= project_birth_min_turns
        and (
            kind in ("business_consulting", "product_creation")
            or _BUSINESS_TOPIC.search(user_message)
        )
    )

    is_casual = kind in _CASUAL_KINDS or kind in _SUPPORT_KINDS
    project_turn = (life.has_project or life.active_path_summary) and (
        _PROJECT_CONTINUE.search(user_message)
        or kind in ("business_consulting", "product_creation", "programming")
    )

    journey_phase = _infer_journey_phase(
        kind=kind,
        user_message=user_message,
        life=life,
        is_casual=is_casual,
        project_turn=project_turn,
        project_birth_ready=project_birth_ready,
        business_depth=business_depth,
    )

    if journey_phase != "open_dialog":
        is_casual = False

    intent, need, action = _compat_routing(
        journey_phase,
        kind=kind,
        project_birth_ready=project_birth_ready,
        life=life,
        is_casual=is_casual,
    )

    priority = _priority_for_phase(
        journey_phase,
        life=life,
        project_birth_ready=project_birth_ready,
    )

    planner = plan_for_human(
        journey_phase=journey_phase,
        life=life,
        priority=priority,
        project_birth_ready=project_birth_ready,
    )

    channel = select_workforce_channel(
        user_message,
        kind=kind,
        need=need,
        action=action,
        has_attachments=has_attachments,
        has_project=life.has_project,
    )
    workforce_task, workforce_tier = channel_to_task(channel)

    return VectorTurnPlan(
        conversation_kind=kind,
        journey_phase=journey_phase,
        intent=intent,
        need=need,
        action=action,
        priority=priority,
        memory_summary=_build_memory_summary(life),
        context_summary=_build_context_summary(
            life, has_attachments=has_attachments, turn_count=turn_count
        ),
        planner=planner,
        workforce_channel=channel,
        workforce_task=workforce_task,
        workforce_tier=workforce_tier,
        project_birth_ready=project_birth_ready,
        is_casual_turn=is_casual,
    )
