"""L1 extraction + value gate — will this make future conversation better?"""

from __future__ import annotations

import re
from typing import Any

from app.integration.genesis_brain.layers.conversation_type import classify_conversation_type
from app.integration.vector_intelligence.person_memory.schema import PersonProfile
from app.integration.vector_intelligence.person_memory.store import PersonMemoryStore
from app.integration.vector_intelligence.pipeline import VectorTurnPlan

_BUDGET = re.compile(
    r"(\d[\d\s]{2,8})\s*(?:тыс|k|€|евро|eur)",
    re.I,
)
_BUDGET_ALT = re.compile(r"бюджет\s*(?:около\s*)?(\d[\d\s]{2,8})", re.I)
_CITY = re.compile(
    r"(?:в|in)\s+(берлин|berlin|мюнхен|munich|гамбург|hamburg|германи|germany)",
    re.I,
)
_VENTURE = re.compile(
    r"(?:открыть|открываю|хочу)\s+(?:кофейн|кафе|ресторан|салон|магазин|бизнес)",
    re.I,
)
_STYLE = re.compile(r"(современн|минимал|классическ|уютн).{0,20}(?:интерьер|стиль|дизайн)", re.I)
_DECISION = re.compile(
    r"(?:решил|решили|договорились|сначала|потом)\s+(.{8,80})",
    re.I,
)
_AGREEMENT = re.compile(
    r"(?:вернёмся|продолжим|на следующей неделе|потом обсудим)",
    re.I,
)
_REGISTER = re.compile(r"(?:зарегистрировал|открыл)\s+(?:компан|firma|gewerbe|ИП)", re.I)
_TEAM = re.compile(r"(\d+)\s+сотрудник", re.I)
_PIVOT = re.compile(
    r"(?:забудь|новый проект|больше не|вместо этого|теперь делаю|переключаюсь)",
    re.I,
)
_FORGET = re.compile(r"(?:забудь|не учитывай|не помни)\s+(.{3,40})", re.I)
_CONFIRM = re.compile(
    r"(?:да,?\s*)?(?:всё ещё|актуально|верно|правильно|именно так)",
    re.I,
)


def should_persist(user_message: str, *, turn: VectorTurnPlan | None = None) -> bool:
    """Gate: сделает ли это будущий разговор лучше?"""
    if turn and turn.is_casual_turn:
        return False
    kind = classify_conversation_type(user_message)
    if kind in (
        "casual_conversation",
        "humor",
        "philosophy",
        "science",
        "general_question",
        "emotional_support",
    ):
        if not _VENTURE.search(user_message) and not _BUDGET.search(user_message):
            return False
    if len((user_message or "").strip()) < 8:
        return False
    return True


def extract_and_apply(
    store: PersonMemoryStore,
    profile: PersonProfile,
    user_message: str,
    *,
    turn: VectorTurnPlan | None = None,
) -> PersonProfile:
    text = (user_message or "").strip()
    if not text or not should_persist(text, turn=turn):
        return profile

    low = text.lower()

    if _PIVOT.search(low):
        profile = store.archive_path(profile)
        profile = store.set_active_path(
            profile,
            summary="Новое направление — уточняем вместе",
            stage="idea",
            confidence=0.45,
        )
        return profile

    forget = _FORGET.search(text)
    if forget:
        hint = forget.group(1).strip().lower()
        if "бюджет" in hint:
            profile = store.forget_key(profile, "budget.primary")
        if "кофейн" in hint or "кафе" in hint:
            profile = store.archive_path(profile)
        return profile

    if _VENTURE.search(text):
        venture = "открывает кофейню" if "кофейн" in low or "кафе" in low else "развивает бизнес"
        if "ресторан" in low:
            venture = "открывает ресторан"
        profile = store.set_active_path(
            profile,
            summary=venture,
            stage="concept" if "концепц" in low else "idea",
            confidence=0.82,
        )
        profile = store.upsert_atom(
            profile,
            category="goals",
            key="goal.primary",
            display=f"Цель: {venture}",
            confidence=0.8,
        )
        profile = store.upsert_atom(
            profile,
            category="projects",
            key="project.venture",
            display=venture,
            confidence=0.82,
        )

    city = _CITY.search(text)
    if city:
        place = city.group(1).capitalize()
        profile = store.upsert_atom(
            profile,
            category="projects",
            key="project.market",
            display=f"Рынок: {place}",
            confidence=0.85,
        )
        if profile.active_path.summary:
            profile = store.set_active_path(
                profile,
                summary=f"{profile.active_path.summary} ({place})",
                stage=profile.active_path.stage,
                confidence=min(0.92, profile.active_path.confidence + 0.05),
            )

    budget_m = _BUDGET.search(text) or _BUDGET_ALT.search(text)
    if budget_m:
        raw = re.sub(r"\s", "", budget_m.group(1))
        try:
            amount = int(raw)
            if amount < 500:
                amount *= 1000
            display = f"бюджет около {amount:,} €".replace(",", " ")
            profile = store.upsert_atom(
                profile,
                category="budget",
                key="budget.primary",
                display=display,
                confidence=0.9,
            )
        except ValueError:
            pass

    if _STYLE.search(low):
        profile = store.upsert_atom(
            profile,
            category="preferences",
            key="pref.style",
            display="современный стиль / интерьер",
            confidence=0.78,
        )

    if _REGISTER.search(low):
        profile = store.set_active_path(
            profile,
            summary=profile.active_path.summary or "Развитие бизнеса",
            stage="registered",
            confidence=0.88,
        )

    team = _TEAM.search(low)
    if team:
        n = team.group(1)
        profile = store.set_active_path(
            profile,
            summary=profile.active_path.summary or "Работающий бизнес",
            stage="operating",
            confidence=0.86,
        )
        profile = store.upsert_atom(
            profile,
            category="projects",
            key="project.team_size",
            display=f"команда: {n} сотрудников",
            confidence=0.8,
        )

    decision = _DECISION.search(text)
    if decision and should_persist(text, turn=turn):
        profile = store.upsert_atom(
            profile,
            category="decisions",
            key=f"decision.{len(profile.atoms)}",
            display=decision.group(1).strip()[:120],
            confidence=0.72,
        )

    if _AGREEMENT.search(low):
        profile = store.upsert_atom(
            profile,
            category="agreements",
            key="agreement.continue",
            display="договорились вернуться к обсуждению",
            confidence=0.75,
        )

    if _CONFIRM.search(low) and profile.atoms:
        for atom in reversed(profile.atoms):
            if atom.status == "stale":
                atom.status = "confirmed"
                atom.confidence = min(0.95, atom.confidence + 0.15)
                break

    return profile
