"""
Journey UX organizer — project passage only, not conversation strategy.

Routes user through Project Execution Journey. No consultant persona.
Facts from public_truth_catalog; business movement from reasoned_reply.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.reasoned_reply import reasoned_business_reply
from app.integration.public_truth_catalog import (
    MISSION1_LANDING_TIMELINE,
    studio_unavailable_message,
    unavailable_online_message,
)
from app.integration.vector_intelligence.types import JourneyPhase

_JOURNEY_CLARIFY: frozenset[JourneyPhase] = frozenset(
    {"understand_goal", "requirements", "materials"}
)


def infer_journey_phase(state: ConversationState, last_user: str) -> JourneyPhase:
    """Map conversation state to Journey phase — UX routing only."""
    low = last_user.lower()
    if not low.strip():
        return "open_dialog"
    if state.goal in ("open_business", "ai_company") or state.needs_website:
        if state.ready_for_business_advice():
            return "requirements"
        missing = state.missing_critical([])
        if missing:
            return "understand_goal"
        return "accept_responsibility"
    if re.search(r"сайт|лендинг|заказ|order|оформ", low):
        if state.has_country() or state.business_type:
            return "requirements"
        return "accept_responsibility"
    if re.search(r"правк|измени|не то|нет\.?$", low):
        return "revisions"
    if re.search(r"готов|запуск|оплат|оформ", low):
        return "launch"
    return "open_dialog"


def journey_ux_reply(
    state: ConversationState,
    last_user: str,
    *,
    messages: list[dict[str, str]] | None = None,
    visitor_id: str = "anonymous",
    turn_index: int = 1,
) -> str | None:
    """
    Single UX entry for project work — continuous collaboration, not chat script.
    Returns None when Journey does not apply (caller continues pipeline).
    """
    low = last_user.lower()
    phase = infer_journey_phase(state, last_user)

    if re.search(r"studio", low) and re.search(r"хочу|нужен|купить|подписк", low):
        return studio_unavailable_message()

    if re.search(r"интернет-магазин|онлайн-магазин", low):
        return unavailable_online_message("Интернет-магазин").replace(
            "после короткой консультации с Vector",
            "когда будете готовы",
        )

    if re.search(r"чат-бот|чатбот|telegram-бот", low) and not re.search(
        r"сайт|лендинг", low
    ):
        return unavailable_online_message("Чат-бот").replace(
            "после короткой консультации с Vector",
            "когда будете готовы",
        )

    if re.search(r"приложен|\bapp\b", low) and "сайт" not in low:
        return unavailable_online_message("Мобильное приложение").replace(
            "после короткой консультации с Vector",
            "когда будете готовы",
        )

    if state.needs_website or state.goal in ("open_business", "ai_company"):
        routed = reasoned_business_reply(
            state,
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=messages,
        )
        if routed:
            return routed

    if phase == "accept_responsibility" and re.search(r"сайт|лендинг", low):
        niche = state.business_type or "бизнеса"
        return (
            f"Принял задачу: сайт для {niche}.\n\n"
            f"Пакеты **350 / 650 / 1200 €** на /order. Срок — {MISSION1_LANDING_TIMELINE}.\n\n"
            "Следующий шаг — уточнить требования или перейти к оформлению."
        )

    if phase in _JOURNEY_CLARIFY:
        return reasoned_business_reply(
            state,
            last_user,
            visitor_id=visitor_id,
            turn_index=turn_index,
            messages=messages,
        )

    return None
