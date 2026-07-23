"""
Decision Intelligence Platform — O → D → D → E

Trust            → что чувствует человек
Decision Intel   → Observation → Diagnosis → Decision → Execution plan
Execution        → Website · CRM · GMB · … (любой deliverable)

Принцип: Vector не продаёт услуги. Он выбирает лучший следующий шаг для компании.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.integration.project_platform.journey_state import (
    extract_city_label,
    extract_company_name,
)
from app.integration.vector_intelligence.industry_intelligence import (
    IndustryProfession,
    build_decision_leadership_response,
    match_industry_profession,
    profession_style_followup,
)

_EXPLICIT_DELIVERABLE = re.compile(
    r"(?:"
    r"сайт|лендинг|website|webseite|"
    r"\bcrm\b|сео|seo|"
    r"чат[- ]?бот|автоматиз|"
    r"ai[- ]?сотрудник|приложени"
    r")",
    re.I,
)

_EXPLICIT_CREATE = re.compile(
    r"(?:создай|создать|сделай|сделать|нужен|нужна|хочу|под ключ|build|create|make)",
    re.I,
)


@dataclass(frozen=True)
class DecisionBrief:
    """O → D → D → E для одной ситуации компании."""

    profession: IndustryProfession
    observation: str
    diagnosis: str
    decision: str
    execution_steps: tuple[str, ...]
    website_first: bool
    recommended_focus: str


def _explicit_deliverable_request(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return bool(_EXPLICIT_DELIVERABLE.search(t) and (_EXPLICIT_CREATE.search(t) or len(t) > 20))


def _observation_line(text: str, prof: IndustryProfession) -> str:
    company = extract_company_name(text)
    city = extract_city_label(text)
    low = (text or "").lower()

    parts: list[str] = []
    if company:
        parts.append(f"компания **{company}**")
    else:
        parts.append(f"**{prof.name_ru.lower()}**")
    if city:
        parts.append(f"рынок — {city}")
    if re.search(r"excel|таблиц", low):
        parts.append("учёт пока вручную")
    if re.search(r"мало клиент|мало заказ|мало заяв", low):
        parts.append("мало входящих заявок")
    if re.search(r"устал|не понимаю|с чего", low):
        parts.append("нужна ясность с чего начать")

    return "Вижу: " + ", ".join(parts) + "."


def _build_brief(text: str, prof: IndustryProfession) -> DecisionBrief:
    low = (text or "").lower()
    explicit_site = bool(re.search(r"сайт|лендинг|website", low))

    if prof.pid == "PD-001":
        diagnosis = (
            "Главная проблема обычно не «нет сайта», а то, что вас не находят "
            "и не доверяют до первого звонка."
        )
        if explicit_site:
            decision = (
                "Сайт нужен — но соберём его вокруг доверия и заявок из вашего региона, "
                "а не красивых общих фраз."
            )
            steps = prof.first_version_moves
            website_first = True
            focus = "website"
        else:
            decision = (
                "Полноценный сайт пока может подождать. Сначала важнее точка присутствия "
                "и доказательства, что вам можно доверять."
            )
            steps = (
                "оформить Google Business Profile",
                "собрать первые 10 отзывов клиентов",
                "сделать простую страницу «Расчёт стоимости»",
                "потом — полноценный сайт",
            )
            website_first = False
            focus = "presence_first"

    elif prof.pid == "PD-002":
        diagnosis = (
            "Главная проблема не в «страницах сайта», а в том, чтобы гость "
            "захотел прийти именно сегодня."
        )
        if explicit_site:
            decision = "Сайт сделаем — но сначала под задачу «прийти сегодня», не под каталог страниц."
            steps = prof.first_version_moves
            website_first = True
            focus = "website"
        else:
            decision = (
                "Сайт может подождать. Сейчас важнее то, что гость видит до визита."
            )
            steps = (
                "QR-меню для зала",
                "фотографии блюд и атмосферы",
                "резервирование столиков в один клик",
                "актуальный Instagram",
                "сайт — на следующем шаге",
            )
            website_first = False
            focus = "presence_first"

    elif prof.pid == "PD-003":
        diagnosis = "Водитель ищет не список услуг, а кому можно доверить машину."
        decision = (
            "Начнём с ясных формулировок от проблемы клиента и прозрачных сроков — "
            + ("это станет основой сайта." if explicit_site else "это можно сделать до большого сайта.")
        )
        steps = prof.first_version_moves if explicit_site else (
            "страница «Замена тормозов за один день» вместо списка услуг",
            "прозрачные сроки и цена диагностики",
            "запись онлайн",
            "сайт — когда поток заявок стабилизируется",
        )
        website_first = explicit_site
        focus = "website" if explicit_site else "presence_first"

    elif prof.pid == "PD-004":
        diagnosis = "Главный барьер — страх первого визита, а не отсутствие информации об услугах."
        decision = (
            "Сначала уберём тревогу: врачи, спокойный тон, простая запись."
            + (" Это станет каркасом сайта." if explicit_site else "")
        )
        steps = prof.first_version_moves
        website_first = True
        focus = "website"

    else:
        diagnosis = prof.core_insight
        decision = "Следующий шаг — то, что быстрее всего усилит доверие и заявки."
        steps = prof.first_version_moves
        website_first = explicit_site
        focus = "website" if explicit_site else "presence_first"

    return DecisionBrief(
        profession=prof,
        observation=_observation_line(text, prof),
        diagnosis=diagnosis,
        decision=decision,
        execution_steps=steps,
        website_first=website_first,
        recommended_focus=focus,
    )


def evaluate_company_situation(text: str) -> DecisionBrief | None:
    prof = match_industry_profession(text)
    if not prof:
        return None
    return _build_brief(text, prof)


def build_decision_intelligence_response(text: str) -> str | None:
    """
    Full O → D → D → E response.
    When website_first=False — Vector does NOT sell the obvious product (T-003 apex).
    """
    brief = evaluate_company_situation(text)
    if not brief:
        return None

    step_lines = "\n".join(f"✓ {s}" for s in brief.execution_steps)
    closing = (
        "Если согласны — начну с этого. Сайт подключим, когда это станет лучшим шагом."
        if not brief.website_first
        else "Если согласны, я начну именно с этого."
    )

    return (
        f"Понял.\n\n"
        f"**Наблюдение.** {brief.observation}\n\n"
        f"**Диагноз.** {brief.diagnosis}\n\n"
        f"**Решение.** {brief.decision}\n\n"
        f"**Первые шаги:**\n{step_lines}\n\n"
        f"{closing}"
    )


def try_decision_intelligence_route(text: str) -> dict | None:
    """
    Route when client describes business without ordering a deliverable.
    Returns chat dict or None (fall through to project execution).
    """
    t = (text or "").strip()
    if len(t) < 12:
        return None

    from app.integration.website_analysis_v1 import is_commercial_website_repair_query

    if is_commercial_website_repair_query(t):
        return None

    if _explicit_deliverable_request(t):
        return None

    brief = evaluate_company_situation(t)
    if not brief or brief.website_first:
        return None

    answer = build_decision_intelligence_response(t)
    if not answer:
        return None

    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": None,
        "cta_label": None,
        "context": {
            "decision_intelligence": True,
            "observation": brief.observation,
            "diagnosis": brief.diagnosis,
            "recommended_focus": brief.recommended_focus,
            "website_first": brief.website_first,
            "profession_id": brief.profession.pid,
        },
    }


def build_deliverable_path_response(text: str) -> str | None:
    """When client explicitly asks for site — Decision Intel frames, then website path."""
    if not _explicit_deliverable_request(text):
        return None
    lead = build_decision_leadership_response(text)
    if not lead:
        return None
    followup = profession_style_followup(text)
    if followup:
        return f"{lead}\n\n{followup}"
    return lead
