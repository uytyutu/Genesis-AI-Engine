"""
Industry Intelligence — Professional Decision Backlog.

Три слоя Virtus Core:
  Trust Backlog          → что чувствует человек
  Professional Decision  → как мыслит хороший руководитель в отрасли
  Execution Backlog      → как система превращает это в результат

Vector знает как вести проект. Отрасль — набор профессиональных эвристик.

Архитектура:
  Vector → Project Leadership → Industry Intelligence → Website | CRM | …
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.integration.project_platform.journey_state import (
    extract_city_label,
    extract_company_name,
    extract_industry_label,
)


@dataclass(frozen=True)
class IndustryProfession:
    """Decision Model — не статья, а способ мышления руководителя в отрасли."""

    pid: str
    name_ru: str
    pattern: re.Pattern[str]
    activity: str
    leader_decisions: tuple[str, ...]
    core_insight: str
    first_version_moves: tuple[str, ...]
    primary_cta: str
    style_followup: str


# Professional Decision Backlog — PD-001 … PD-005
_PROFESSIONS: tuple[IndustryProfession, ...] = (
    IndustryProfession(
        pid="PD-001",
        name_ru="Строительство",
        pattern=re.compile(r"(строитель|ремонт|бригад|handwerk|bau)", re.I),
        activity="ремонтом",
        leader_decisions=(
            "Как быстрее вызвать доверие?",
            "Как показать реальные объекты?",
            "Как сократить количество пустых звонков?",
            "Как получать заявки только по своему региону?",
        ),
        core_insight=(
            "Для таких компаний главная задача обычно не «сделать сайт», "
            "а вызвать доверие до первого звонка."
        ),
        first_version_moves=(
            "реальные фотографии работ",
            "отзывы клиентов",
            "кнопка «Получить расчёт стоимости»",
        ),
        primary_cta="Получить расчёт стоимости",
        style_followup=(
            "Визуально — **светлый минимализм**, чтобы фотографии работ смотрелись честно. "
            "Подходит или хотите другой тон?"
        ),
    ),
    IndustryProfession(
        pid="PD-002",
        name_ru="Ресторан",
        pattern=re.compile(r"(кафе|кофе|ресторан|cafe|бар\b)", re.I),
        activity="общепитом",
        leader_decisions=(
            "Как сделать так, чтобы гость захотел прийти именно сегодня?",
            "Как показать атмосферу, а не только меню?",
            "Как увеличить средний чек без давления?",
        ),
        core_insight=(
            "Владелец ресторана думает не о «страницах сайта», а о желании прийти сегодня. "
            "Меню должно открываться максимум за два нажатия — иначе часть гостей уйдёт."
        ),
        first_version_moves=(
            "меню на видном месте — не глубже двух кликов",
            "фото блюд и атмосферы",
            "кнопка «Забронировать стол»",
        ),
        primary_cta="Забронировать стол",
        style_followup=(
            "Стиль — **тёплый современный**: уютно, но не устарело. "
            "Или предпочитаете другой характер?"
        ),
    ),
    IndustryProfession(
        pid="PD-003",
        name_ru="Автосервис",
        pattern=re.compile(r"(автосервис|автомобил|шиномонтаж|sto\b|werkstatt)", re.I),
        activity="ремонтом автомобилей",
        leader_decisions=(
            "Как сделать так, чтобы водитель доверил мне машину?",
            "Как показать сроки и цену без сюрпризов?",
            "Как сократить пустые обращения?",
        ),
        core_insight=(
            "Водитель ищет не список услуг, а решение проблемы. "
            "«Замена тормозов за один день» работает лучше, чем перечень работ."
        ),
        first_version_moves=(
            "формулировки от проблемы клиента",
            "сроки и прозрачная цена",
            "кнопка «Записаться на диагностику»",
        ),
        primary_cta="Записаться на диагностику",
        style_followup=(
            "Оформление — **деловой и читаемый**: акцент на доверии и сроках. Согласны?"
        ),
    ),
    IndustryProfession(
        pid="PD-004",
        name_ru="Стоматология",
        pattern=re.compile(r"(стоматолог|dental|зуб)", re.I),
        activity="стоматологией",
        leader_decisions=(
            "Как убрать страх первого визита?",
            "Как показать врачей и спокойствие, а не только услуги?",
            "Как упростить запись?",
        ),
        core_insight=(
            "Пациент выбирает не «лечение на сайте», а спокойствие и ясность — "
            "кто врач, сколько стоит первый шаг, как записаться."
        ),
        first_version_moves=(
            "врачи и спокойный тон",
            "цены или «консультация бесплатно»",
            "простая запись на приём",
        ),
        primary_cta="Записаться на приём",
        style_followup=(
            "Визуально — **светлый спокойный** стиль, без медицинского шума. Подходит?"
        ),
    ),
    IndustryProfession(
        pid="PD-005",
        name_ru="Солнечная энергетика",
        pattern=re.compile(r"(солнеч|solar|панел|энерг)", re.I),
        activity="солнечной энергетикой",
        leader_decisions=(
            "Как показать экономию, а не технические детали?",
            "Как вызвать доверие к установке на дом?",
            "Как получать заявки на расчёт, а не пустые звонки?",
        ),
        core_insight=(
            "Клиент покупает не панели, а экономию и надёжность. "
            "Сначала — выгода и примеры объектов, потом детали."
        ),
        first_version_moves=(
            "примеры установок и цифры экономии",
            "отзывы владельцев домов",
            "заявка на расчёт",
        ),
        primary_cta="Получить расчёт",
        style_followup=(
            "Стиль — **светлый технологичный**: чисто, современно, без перегруза. Согласны?"
        ),
    ),
)


def match_industry_profession(text: str) -> IndustryProfession | None:
    t = text or ""
    # Website Repair commercial queries must not match Bau/Handwerk via «ремонт».
    from app.integration.website_analysis_v1 import is_commercial_website_repair_query

    if is_commercial_website_repair_query(t):
        return None
    for prof in _PROFESSIONS:
        if prof.pattern.search(t):
            return prof
    return None


def list_professions() -> tuple[IndustryProfession, ...]:
    return _PROFESSIONS


def _subject_line(text: str, prof: IndustryProfession) -> str:
    company = extract_company_name(text)
    city = extract_city_label(text)
    industry = extract_industry_label(text)

    if company and city:
        return f"**{company}** занимается {prof.activity} в {city}."
    if company:
        return f"**{company}** занимается {prof.activity}."
    if industry and city:
        return f"Ваша {industry} в {city}."
    if industry:
        return f"Ваша {industry}."
    if city:
        return f"Вы занимаетесь {prof.activity} в {city}."
    return f"Вы занимаетесь {prof.activity}."


def build_decision_leadership_response(text: str) -> str | None:
    """
    Project Leadership + Industry Intelligence.
    Reflection → professional decision → first version moves.
    """
    prof = match_industry_profession(text)
    if not prof:
        return None

    subject = _subject_line(text, prof)
    move_lines = "\n".join(f"• {m};" for m in prof.first_version_moves)
    return (
        f"Понял.\n\n"
        f"{subject}\n\n"
        f"{prof.core_insight}\n\n"
        f"Поэтому я предлагаю строить первую версию вокруг трёх вещей:\n\n"
        f"{move_lines}\n\n"
        f"Если согласны, я начну именно с этого."
    )


def profession_style_followup(text: str) -> str | None:
    prof = match_industry_profession(text)
    if not prof:
        return None
    return prof.style_followup


# Backward-compatible aliases (Knowledge → Decision Model migration)
match_profession_insight = match_industry_profession
build_profession_surprise = build_decision_leadership_response
