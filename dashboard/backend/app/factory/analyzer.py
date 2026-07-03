"""Analyze owner request and pick landing template niche."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisResult:
    niche: str
    template_id: str
    business_name: str
    headline: str
    subtitle: str
    services: list[str]
    cta_label: str
    trust_points: tuple[str, ...]


_NICHE_KEYWORDS = {
    "dental": ("стоматолог", "dental", "зуб", "клиник", "имплант", "ортодонт"),
    "auto": ("автосервис", "авто", "машин", "ремонт авто", "шиномонтаж", "car service", "garage"),
    "beauty": ("салон", "красот", "spa", "маникюр", "парикмахер"),
}


def analyze(description: str) -> AnalysisResult:
    text = description.strip()
    lower = text.lower()

    niche = "generic"
    for name, words in _NICHE_KEYWORDS.items():
        if any(w in lower for w in words):
            niche = name
            break

    business_name = _extract_business_name(text, niche)
    template_id = f"landing-{niche}-v1"

    presets = {
        "dental": AnalysisResult(
            niche="dental",
            template_id=template_id,
            business_name=business_name,
            headline=f"{business_name}",
            subtitle="Без боли и скрытых доплат — прозрачные цены и гарантия на лечение",
            services=[
                "Лечение без страха — бережная анестезия",
                "Прозрачный план лечения до начала работ",
                "Имплантация и эстетика с гарантией",
                "Онлайн-запись за 2 минуты",
            ],
            cta_label="Записаться на приём",
            trust_points=("Опытные врачи", "Современное оборудование", "Гарантия на работу"),
        ),
        "auto": AnalysisResult(
            niche="auto",
            template_id=template_id,
            business_name=business_name,
            headline=f"{business_name}",
            subtitle="Честная смета до начала ремонта — диагностика и гарантия на работу",
            services=[
                "Компьютерная диагностика за 30 минут",
                "Ремонт двигателя и ходовой под ключ",
                "Плановое ТО без навязанных услуг",
                "Шиномонтаж и хранение колёс",
            ],
            cta_label="Записаться в сервис",
            trust_points=("Гарантия на ремонт", "Честная цена", "Опытные мастера"),
        ),
        "beauty": AnalysisResult(
            niche="beauty",
            template_id=template_id,
            business_name=business_name,
            headline=f"{business_name}",
            subtitle="Стиль и забота — мастера, которым доверяют постоянные клиенты",
            services=["Стрижки и укладки", "Маникюр и педикюр", "Уход за кожей", "Подарочные сертификаты"],
            cta_label="Записаться",
            trust_points=("Стерильность", "Премиум-материалы", "Уютная атмосфера"),
        ),
    }

    if niche in presets:
        base = presets[niche]
        return AnalysisResult(
            niche=base.niche,
            template_id=base.template_id,
            business_name=business_name,
            headline=business_name,
            subtitle=_merge_subtitle(base.subtitle, text),
            services=base.services,
            cta_label=base.cta_label,
            trust_points=base.trust_points,
        )

    return AnalysisResult(
        niche="generic",
        template_id="landing-generic-v1",
        business_name=business_name,
        headline=business_name,
        subtitle=_merge_subtitle("Решение для вашего бизнеса — понятно клиентам с первого экрана", text),
        services=[
            "Сильное предложение на главном экране",
            "Современный дизайн и адаптивная вёрстка",
            "Быстрая связь и призыв к действию",
            "Готовность к публикации после вашего одобрения",
        ],
        cta_label="Связаться с нами",
        trust_points=("Быстрый старт", "Прозрачные условия", "Поддержка"),
    )


def _extract_business_name(text: str, niche: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    for prefix in ("мне нужен сайт для ", "хочу лендинг для ", "сайт для ", "лендинг для "):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip(" .")
            break
    if len(cleaned) > 48:
        cleaned = cleaned[:45] + "…"
    if not cleaned:
        defaults = {"dental": "Стоматология", "auto": "Автосервис", "beauty": "Салон красоты"}
        return defaults.get(niche, "Ваш бизнес")
    return cleaned[0].upper() + cleaned[1:]


def _merge_subtitle(default: str, raw: str) -> str:
    if len(raw) > 20 and raw not in default:
        return f"{default}. {raw[:120]}"
    return default
