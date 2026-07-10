"""Welcome experience — dialog wizard and personalization."""

from __future__ import annotations

from app.integration.customer_identity.schema import (
    QUICK_ACTIONS_BY_PROFILE,
    WIZARD_QUESTIONS_RU,
    WIZARD_STEPS,
    InferredProfile,
    WelcomePhase,
    WelcomeSession,
)

_ENTREPRENEUR_MARKERS = (
    "бизнес",
    "кафе",
    "магазин",
    "предприним",
    "компани",
    "стартап",
    "услуг",
    "клиент",
    "продаж",
    "business",
    "shop",
    "restaurant",
)
_DESIGNER_MARKERS = (
    "дизайн",
    "портфолио",
    "креатив",
    "бренд",
    "визуал",
    "design",
    "portfolio",
    "ui",
    "ux",
)
_DEVELOPER_MARKERS = (
    "разработ",
    "програм",
    "api",
    "код",
    "приложен",
    "developer",
    "software",
    "engineer",
)


def infer_profile(answers: dict[str, str]) -> InferredProfile:
    blob = " ".join(answers.values()).lower()
    if any(m in blob for m in _DEVELOPER_MARKERS):
        return "developer"
    if any(m in blob for m in _DESIGNER_MARKERS):
        return "designer"
    if any(m in blob for m in _ENTREPRENEUR_MARKERS):
        return "entrepreneur"
    pace = (answers.get("pace") or "").lower()
    if "познаком" in pace or "обзор" in pace:
        return "explorer"
    return "entrepreneur"


def greeting_message(name: str) -> str:
    first = (name or "").strip().split()[0] if name else "друг"
    return (
        "Добро пожаловать в Virtus Core.\n\n"
        f"Здравствуйте, {first}.\n"
        "Я Vector.\n"
        "Сегодня мы создадим вашу цифровую компанию."
    )


def headline_ready() -> str:
    return "Ваша цифровая компания готова."


def current_wizard_question(session: WelcomeSession) -> str | None:
    if session.phase != "wizard":
        return None
    if session.wizard_step_index >= len(WIZARD_STEPS):
        return None
    step = WIZARD_STEPS[session.wizard_step_index]
    return WIZARD_QUESTIONS_RU[step]


def advance_welcome(session: WelcomeSession) -> WelcomeSession:
    if session.phase == "greeting":
        session.phase = "wizard"
        session.wizard_step_index = 0
        return session
    if session.phase == "wizard":
        session.wizard_step_index += 1
        if session.wizard_step_index >= len(WIZARD_STEPS):
            session.inferred_profile = infer_profile(session.wizard_answers)
            session.quick_actions = list(QUICK_ACTIONS_BY_PROFILE[session.inferred_profile])
            session.phase = "personalized"
        return session
    if session.phase == "personalized":
        session.phase = "complete"
    return session


def apply_wizard_answer(session: WelcomeSession, answer: str) -> WelcomeSession:
    if session.phase != "wizard":
        return session
    if session.wizard_step_index >= len(WIZARD_STEPS):
        return session
    step = WIZARD_STEPS[session.wizard_step_index]
    session.wizard_answers[step] = (answer or "").strip()[:500]
    return advance_welcome(session)


def welcome_payload(session: WelcomeSession, *, name: str) -> dict:
    phase: WelcomePhase = session.phase
    payload: dict = {
        "phase": phase,
        "headline": headline_ready() if phase != "greeting" else None,
        "message": greeting_message(name) if phase == "greeting" else None,
        "wizard_question": current_wizard_question(session),
        "wizard_step": session.wizard_step_index + 1 if phase == "wizard" else None,
        "wizard_total": len(WIZARD_STEPS) if phase == "wizard" else None,
        "can_skip": phase == "wizard",
        "quick_actions": session.quick_actions if phase in ("personalized", "complete") else [],
        "complete": phase == "complete",
    }
    if phase == "personalized":
        payload["message"] = (
            "Отлично. Ваша компания настроена под вас.\n"
            "Выберите, с чего начнём — или просто напишите Vector."
        )
    return payload
