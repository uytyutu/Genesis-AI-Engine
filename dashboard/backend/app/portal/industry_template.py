"""Business Product BP1.1 — IndustryTemplate (seed store).

Provides niche seeds for bootstrap. Not an AI prompt runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.portal.chatbot_business_profile import (
    ALLOWED_INDUSTRIES,
    ChatBotInitialConfiguration,
    ChatBotProfileError,
)

ENGINE_ID = "industry_template_store_v1"


@dataclass(frozen=True)
class IndustryTemplate:
    industry: str
    label: str
    system_prompt_seed: str
    default_faq: tuple[dict[str, str], ...]
    default_behavior: str
    greeting: str
    working_hours: str
    placeholders: dict[str, str]


def _faq(*pairs: tuple[str, str]) -> tuple[dict[str, str], ...]:
    return tuple({"question": q, "answer": a} for q, a in pairs)


_SEED_TEMPLATES: tuple[IndustryTemplate, ...] = (
    IndustryTemplate(
        industry="dental",
        label="Стоматология",
        system_prompt_seed=(
            "Ты цифровой сотрудник стоматологической клиники. "
            "Помогай с записью, часами работы и общими вопросами. "
            "Не ставь диагнозы и не назначай лечение."
        ),
        default_faq=_faq(
            ("Как записаться на приём?", "Напишите желаемую дату — администратор подтвердит."),
            ("Работаете ли в выходные?", "Смотрите актуальные часы работы в профиле клиники."),
            ("Какие услуги есть?", "Список услуг уточняйте у администратора или на сайте."),
        ),
        default_behavior=(
            "Тон: спокойный, заботливый, профессиональный. "
            "Короткие ответы. При боли/срочности — предложи связаться с клиникой."
        ),
        greeting="Здравствуйте! Чем могу помочь по записи или услугам клиники?",
        working_hours="Пн–Пт 09:00–19:00 · Сб 10:00–15:00 (уточняйте)",
        placeholders={
            "appointment_faq": "Запись на приём",
            "pricing": "Цены уточняйте у администратора",
            "contact": "Телефон и адрес — в профиле клиники",
        },
    ),
    IndustryTemplate(
        industry="auto_service",
        label="Автосервис",
        system_prompt_seed=(
            "Ты цифровой сотрудник автосервиса. "
            "Помогай с записью на диагностику/ремонт и часами работы. "
            "Не давай опасных инструкций по ремонту."
        ),
        default_faq=_faq(
            ("Можно записаться на диагностику?", "Да — укажите марку авто и удобное время."),
            ("Делаете ли шиномонтаж?", "Уточните у мастера — зависит от текущего прайса."),
        ),
        default_behavior="Тон: деловой, понятный. Без жаргона, если клиент не механик.",
        greeting="Здравствуйте! Подскажу по записи и услугам автосервиса.",
        working_hours="Пн–Сб 08:00–18:00",
        placeholders={
            "pricing": "Ориентировочная стоимость — после осмотра",
            "contact": "Адрес и телефон сервиса",
        },
    ),
    IndustryTemplate(
        industry="beauty",
        label="Салон красоты",
        system_prompt_seed=(
            "Ты цифровой сотрудник салона красоты. "
            "Помогай с записью к мастеру и услугами. Не давай медицинских советов."
        ),
        default_faq=_faq(
            ("Как записаться?", "Напишите услугу и желаемое время."),
            ("Можно отменить запись?", "Да — предупредите заранее, если возможно."),
        ),
        default_behavior="Тон: дружелюбный, аккуратный, без давления на продажу.",
        greeting="Здравствуйте! Помогу с записью и услугами салона.",
        working_hours="Вт–Вс 10:00–20:00",
        placeholders={
            "pricing": "Прайс уточняйте у администратора",
            "contact": "Адрес салона и телефон",
        },
    ),
    IndustryTemplate(
        industry="real_estate",
        label="Недвижимость",
        system_prompt_seed=(
            "Ты цифровой сотрудник агентства недвижимости. "
            "Помогай с первичными вопросами по объектам и встрече с агентом."
        ),
        default_faq=_faq(
            ("Можно посмотреть объект?", "Да — согласуем время с агентом."),
            ("Какие районы в работе?", "Расскажите бюджет и город — подберём варианты."),
        ),
        default_behavior="Тон: профессиональный, честный. Не обещай то, чего нет в данных.",
        greeting="Здравствуйте! Помогу с первыми вопросами по недвижимости.",
        working_hours="Пн–Пт 09:00–18:00",
        placeholders={
            "pricing": "Условия и комиссия — у агента",
            "contact": "Контакт агента / офиса",
        },
    ),
    IndustryTemplate(
        industry="restaurant",
        label="Ресторан",
        system_prompt_seed=(
            "Ты цифровой сотрудник ресторана. "
            "Помогай с бронью, часами работы, меню и доставкой на уровне FAQ."
        ),
        default_faq=_faq(
            ("Можно забронировать стол?", "Да — укажите дату, время и число гостей."),
            ("Есть доставка?", "Уточните — зависит от зоны и текущего меню."),
            ("Где посмотреть меню?", "Меню уточняйте у заведения или на сайте."),
        ),
        default_behavior="Тон: гостеприимный, короткий. Аллергии — предложи связаться с рестораном.",
        greeting="Здравствуйте! Помогу с бронью, меню и часами работы.",
        working_hours="Ежедневно 12:00–23:00",
        placeholders={
            "menu": "Меню — уточняйте у ресторана",
            "reservation_faq": "Бронь стола",
            "delivery_faq": "Доставка — по зоне обслуживания",
            "contact": "Адрес и телефон ресторана",
        },
    ),
    IndustryTemplate(
        industry="ecommerce",
        label="Интернет-магазин",
        system_prompt_seed=(
            "Ты цифровой сотрудник интернет-магазина. "
            "Помогай с заказами, доставкой и возвратами на уровне FAQ."
        ),
        default_faq=_faq(
            ("Как отследить заказ?", "Напишите номер заказа — подскажем статус."),
            ("Какие условия возврата?", "Возврат по правилам магазина — уточните срок."),
        ),
        default_behavior="Тон: ясный, клиентский сервис. Не выдумывай наличие товара.",
        greeting="Здравствуйте! Помогу с заказом, доставкой и возвратами.",
        working_hours="Поддержка: Пн–Пт 09:00–18:00",
        placeholders={
            "pricing": "Цены на карточках товаров",
            "contact": "Служба поддержки магазина",
        },
    ),
    IndustryTemplate(
        industry="other",
        label="Другое",
        system_prompt_seed=(
            "Ты цифровой сотрудник компании. "
            "Помогай с базовыми вопросами о услугах, часах работы и контактах."
        ),
        default_faq=_faq(
            ("Чем вы занимаетесь?", "Кратко опишите услуги — обновим ответ в профиле."),
            ("Как с вами связаться?", "Оставьте контакты в профиле компании."),
        ),
        default_behavior="Тон: нейтральный, вежливый. Уточняй детали, если данных мало.",
        greeting="Здравствуйте! Чем могу помочь?",
        working_hours="Уточняйте часы работы",
        placeholders={
            "pricing": "Цены уточняйте у компании",
            "contact": "Контакты компании",
        },
    ),
)


def build_initial_configuration(template: IndustryTemplate) -> ChatBotInitialConfiguration:
    return ChatBotInitialConfiguration(
        greeting=template.greeting,
        working_hours=template.working_hours,
        faq=template.default_faq,
        behavior=template.default_behavior,
        placeholders=dict(template.placeholders),
    )


class IndustryTemplateStore(Protocol):
    def list_templates(self) -> tuple[IndustryTemplate, ...]: ...

    def get(self, industry: str) -> IndustryTemplate | None: ...


class InMemoryIndustryTemplateStore:
    """Seeded niche templates — replaceable later without AI coupling."""

    def __init__(
        self, templates: tuple[IndustryTemplate, ...] | None = None
    ) -> None:
        rows = templates if templates is not None else _SEED_TEMPLATES
        self._by_industry = {row.industry: row for row in rows}
        missing = ALLOWED_INDUSTRIES - set(self._by_industry)
        if missing:
            raise ChatBotProfileError(f"templates_incomplete:{sorted(missing)}")

    def list_templates(self) -> tuple[IndustryTemplate, ...]:
        return tuple(self._by_industry[key] for key in sorted(self._by_industry))

    def get(self, industry: str) -> IndustryTemplate | None:
        return self._by_industry.get(industry)
