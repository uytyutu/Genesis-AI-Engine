"""Client bot setup from questionnaire — Virtus Core digital employee onboarding.

Deterministic: answers → greeting + system prompt + config + knowledge rows.
No CEO approve. No LLM required to assemble the first employee brief.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.chatbot_business_profile import (
    ALLOWED_INDUSTRIES,
    ChatBotInitialConfiguration,
    ChatBotProfileError,
)
from app.portal.industry_template import InMemoryIndustryTemplateStore

ENGINE_ID = "bot_setup_questionnaire_v1"

_TONE_LABELS: dict[str, str] = {
    "formal": "официальный, сдержанный",
    "friendly": "дружелюбный, тёплый",
    "professional_friendly": "профессиональный и дружелюбный",
    "casual": "простой, разговорный",
}

_LANG_LABELS: dict[str, str] = {
    "de": "немецкий",
    "ru": "русский",
    "en": "английский",
    "uk": "украинский",
    "pl": "польский",
}


@dataclass(frozen=True)
class BotSetupAnswers:
    business_name: str
    what_company_does: str
    services: str
    answer_topics: str
    avoid_topics: str
    working_hours: str
    address: str = ""
    phone: str = ""
    website: str = ""
    language: str = "de"
    tone: str = "professional_friendly"
    industry: str = "other"
    book_appointments: bool = True
    take_leads: bool = True
    give_prices: bool = False
    timezone: str = "Europe/Berlin"

    def as_dict(self) -> dict[str, Any]:
        return {
            "business_name": self.business_name,
            "what_company_does": self.what_company_does,
            "services": self.services,
            "answer_topics": self.answer_topics,
            "avoid_topics": self.avoid_topics,
            "working_hours": self.working_hours,
            "address": self.address,
            "phone": self.phone,
            "website": self.website,
            "language": self.language,
            "tone": self.tone,
            "industry": self.industry,
            "book_appointments": self.book_appointments,
            "take_leads": self.take_leads,
            "give_prices": self.give_prices,
            "timezone": self.timezone,
        }


def parse_answers(raw: dict[str, Any] | None) -> BotSetupAnswers:
    data = raw if isinstance(raw, dict) else {}
    name = str(data.get("business_name") or "").strip()
    if not name:
        raise ChatBotProfileError("business_name_required")
    industry = str(data.get("industry") or "other").strip().lower() or "other"
    if industry not in ALLOWED_INDUSTRIES:
        industry = "other"
    from app.integration.locale_service import resolve_generation_language

    lang = resolve_generation_language(data.get("language"), default="en")
    tone = str(data.get("tone") or "professional_friendly").strip() or "professional_friendly"
    if tone not in _TONE_LABELS:
        tone = "professional_friendly"
    return BotSetupAnswers(
        business_name=name,
        what_company_does=str(data.get("what_company_does") or "").strip(),
        services=str(data.get("services") or "").strip(),
        answer_topics=str(data.get("answer_topics") or "").strip(),
        avoid_topics=str(data.get("avoid_topics") or "").strip(),
        working_hours=str(data.get("working_hours") or "").strip() or "Уточняйте часы работы",
        address=str(data.get("address") or "").strip(),
        phone=str(data.get("phone") or "").strip(),
        website=str(data.get("website") or "").strip(),
        language=lang[:8],
        tone=tone,
        industry=industry,
        book_appointments=bool(data.get("book_appointments", True)),
        take_leads=bool(data.get("take_leads", True)),
        give_prices=bool(data.get("give_prices", False)),
        timezone=str(data.get("timezone") or "Europe/Berlin").strip() or "Europe/Berlin",
    )


def _contact_line(answers: BotSetupAnswers) -> str:
    parts = [p for p in (answers.address, answers.phone, answers.website) if p]
    return " · ".join(parts)


def build_greeting(answers: BotSetupAnswers) -> str:
    lang = answers.language
    name = answers.business_name
    if lang == "de":
        return (
            f"Willkommen bei {name}. Ich bin der digitale Mitarbeiter. "
            f"Ich helfe bei Fragen zu Leistungen, Öffnungszeiten und Kontakt."
        )
    if lang == "en":
        return (
            f"Welcome to {name}. I am your digital employee. "
            f"I can help with services, hours, and contact."
        )
    # ru / default
    jobs: list[str] = []
    if answers.book_appointments:
        jobs.append("записаться")
    if answers.take_leads:
        jobs.append("оставить заявку")
    if answers.give_prices:
        jobs.append("узнать ориентир по ценам")
    jobs.append("ответить на вопросы об услугах")
    help_bit = ", ".join(jobs[:-1]) + (f" и {jobs[-1]}" if len(jobs) > 1 else jobs[0])
    return (
        f"Добро пожаловать в {name}. Я цифровой помощник. "
        f"Помогаю {help_bit}. "
        f"Если вопрос требует сотрудника, передам заявку команде."
    )


def build_system_prompt(answers: BotSetupAnswers) -> str:
    template = InMemoryIndustryTemplateStore().get(answers.industry)
    seed = template.system_prompt_seed if template else (
        "Ты цифровой сотрудник компании. Помогай с базовыми вопросами."
    )
    tone = _TONE_LABELS.get(answers.tone, answers.tone)
    lang_label = _LANG_LABELS.get(answers.language, answers.language)
    capabilities: list[str] = []
    if answers.book_appointments:
        capabilities.append("помогать с записью / бронированием")
    if answers.take_leads:
        capabilities.append("принимать заявки и контакт клиента")
    if answers.give_prices:
        capabilities.append("давать ориентировочные цены, если они есть в знаниях")
    else:
        capabilities.append("не называть точные цены — предложить связаться с компанией")

    lines = [
        f"Ты — цифровой сотрудник компании «{answers.business_name}» (Virtus Core / Vector).",
        seed,
        f"Язык ответов: {lang_label} ({answers.language}).",
        f"Тон: {tone}.",
        f"Чем занимается компания: {answers.what_company_does or 'см. услуги ниже'}.",
        f"Услуги: {answers.services or 'уточнять у компании'}.",
        f"Часы работы: {answers.working_hours}.",
    ]
    contact = _contact_line(answers)
    if contact:
        lines.append(f"Контакты: {contact}.")
    if answers.answer_topics:
        lines.append(f"Отвечай уверенно на темы: {answers.answer_topics}.")
    if answers.avoid_topics:
        lines.append(
            f"Не обсуждай и вежливо откажись от тем: {answers.avoid_topics}. "
            f"Предложи связаться с сотрудником."
        )
    lines.append("Твои задачи: " + "; ".join(capabilities) + ".")
    lines.append(
        "Не выдумывай факты, которых нет в анкете и знаниях. "
        "Если данных нет — скажи об этом и предложи контакт компании."
    )
    return "\n".join(lines)


def build_configuration(answers: BotSetupAnswers) -> ChatBotInitialConfiguration:
    template = InMemoryIndustryTemplateStore().get(answers.industry)
    greeting = build_greeting(answers)
    behavior = (
        f"Тон: {_TONE_LABELS.get(answers.tone, answers.tone)}. "
        f"Язык: {answers.language}. "
        + (template.default_behavior if template else "")
    ).strip()
    faq = list(template.default_faq) if template else []
    if answers.services:
        faq = [{"question": "Какие услуги вы оказываете?", "answer": answers.services}, *faq]
    placeholders = dict(template.placeholders) if template else {}
    placeholders.update(
        {
            "system_prompt": build_system_prompt(answers),
            "setup_status": "draft",
            "tone": answers.tone,
            "contact": _contact_line(answers) or placeholders.get("contact", ""),
            "pricing": (
                "Цены можно обсуждать по знаниям компании"
                if answers.give_prices
                else "Точные цены — у сотрудника компании"
            ),
        }
    )
    return ChatBotInitialConfiguration(
        greeting=greeting,
        working_hours=answers.working_hours,
        faq=tuple(faq[:8]),
        behavior=behavior,
        placeholders=placeholders,
    )


def knowledge_rows(answers: BotSetupAnswers) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    if answers.what_company_does:
        rows.append(
            {
                "category": "company",
                "title": "О компании",
                "content": answers.what_company_does,
            }
        )
    if answers.services:
        rows.append(
            {
                "category": "services",
                "title": "Услуги",
                "content": answers.services,
            }
        )
    rows.append(
        {
            "category": "working_hours",
            "title": "Часы работы",
            "content": answers.working_hours,
        }
    )
    contact = _contact_line(answers)
    if contact:
        rows.append(
            {
                "category": "contacts",
                "title": "Контакты",
                "content": contact,
            }
        )
    if answers.answer_topics:
        rows.append(
            {
                "category": "faq",
                "title": "Темы для ответов",
                "content": answers.answer_topics,
            }
        )
    if answers.avoid_topics:
        rows.append(
            {
                "category": "policies",
                "title": "Не обсуждать",
                "content": answers.avoid_topics,
            }
        )
    rows.append(
        {
            "category": "company",
            "title": "Digital employee brief",
            "content": build_system_prompt(answers),
        }
    )
    return rows


def build_setup_preview(raw: dict[str, Any] | None) -> dict[str, Any]:
    answers = parse_answers(raw)
    config = build_configuration(answers)
    prompt = build_system_prompt(answers)
    greeting = build_greeting(answers)
    return {
        "ok": True,
        "engine": ENGINE_ID,
        "status": "preview",
        "answers": answers.as_dict(),
        "greeting": greeting,
        "system_prompt": prompt,
        "configuration": config.as_dict(),
        "knowledge_preview": knowledge_rows(answers),
        "capabilities": {
            "book_appointments": answers.book_appointments,
            "take_leads": answers.take_leads,
            "give_prices": answers.give_prices,
        },
        "note_ru": (
            "Превью собрано из анкеты. Нажмите «Опубликовать» — "
            "бот станет доступен без одобрения владельца Virtus."
        ),
    }
