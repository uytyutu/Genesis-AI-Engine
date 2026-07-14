"""Micro-task / labeling platform registry — honest setup, no fake connections."""

from __future__ import annotations

import os
from typing import Any

# Real platforms where data labeling / micro-tasks pay per result.
# Genesis connects only when CEO adds API keys to .env.local — never auto-faked.
PLATFORM_REGISTRY: list[dict[str, Any]] = [
    {
        "id": "internal_queue",
        "label": "Virtus Core (внутренняя очередь)",
        "category": "labeling",
        "status_key": None,
        "env_var": None,
        "pay_hint": "0.05 € / разметка (учебный режим)",
        "signup_url": None,
        "steps": [
            "Уже работает — сырьё из сканов Genesis.",
            "Нажми «Запустить ферму» на главной.",
        ],
        "note": "Без регистрации. Комбайны размечают тексты из очереди.",
    },
    {
        "id": "scale_ai",
        "label": "Scale AI",
        "category": "labeling",
        "status_key": "SCALE_API_KEY",
        "env_var": "SCALE_API_KEY",
        "pay_hint": "от $0.01 за объект разметки",
        "signup_url": "https://scale.com/",
        "steps": [
            "Зарегистрируйся на scale.com как Contributor или API customer.",
            "В Dashboard → API Keys создай ключ.",
            "Вставь в dashboard/backend/.env.local: SCALE_API_KEY=...",
            "Перезапусти Genesis.exe.",
        ],
        "note": "Крупнейшая биржа разметки для обучения ИИ. Нужен одобренный аккаунт.",
    },
    {
        "id": "toloka",
        "label": "Toloka (Yandex)",
        "category": "microtask",
        "status_key": "TOLOKA_API_TOKEN",
        "env_var": "TOLOKA_API_TOKEN",
        "pay_hint": "микро-задачи, выплаты на кошелёк",
        "signup_url": "https://toloka.ai/",
        "steps": [
            "Аккаунт на toloka.ai → API access (для заказчика/исполнителя по правилам Toloka).",
            "Скопируй OAuth token / API token.",
            ".env.local: TOLOKA_API_TOKEN=...",
            "Перезапусти Genesis.",
        ],
        "note": "Подходит для массовой разметки текстов и изображений.",
    },
    {
        "id": "appen",
        "label": "Appen Connect",
        "category": "labeling",
        "status_key": "APPEN_API_KEY",
        "env_var": "APPEN_API_KEY",
        "pay_hint": "проектная оплата за batch",
        "signup_url": "https://appen.com/",
        "steps": [
            "Регистрация на appen.com → одобрение профиля (может занять дни).",
            "Получи API/crowd credentials от менеджера проекта.",
            ".env.local: APPEN_API_KEY=...",
        ],
        "note": "Enterprise — часто нужен ручной онбординг с Appen.",
    },
    {
        "id": "mturk",
        "label": "Amazon MTurk",
        "category": "microtask",
        "status_key": "AWS_ACCESS_KEY_ID",
        "env_var": "MTURK_AWS_SECRET_ACCESS_KEY",
        "pay_hint": "HIT-микрозадачи",
        "signup_url": "https://requester.mturk.com/",
        "steps": [
            "AWS аккаунт + MTurk Requester sandbox или production.",
            "IAM ключи с доступом к MTurk API.",
            ".env.local: AWS_ACCESS_KEY_ID=... MTURK_AWS_SECRET_ACCESS_KEY=...",
            "Регион: us-east-1 для Requester API.",
        ],
        "note": "Строгие правила: боты запрещены в ToS — только легальные HIT как requester.",
    },
    {
        "id": "hive",
        "label": "Hive Data",
        "category": "labeling",
        "status_key": "HIVE_API_KEY",
        "env_var": "HIVE_API_KEY",
        "pay_hint": "разметка модерация контента",
        "signup_url": "https://thehive.ai/",
        "steps": [
            "Контакт sales / API на thehive.ai.",
            "Получи API key для data labeling endpoints.",
            ".env.local: HIVE_API_KEY=...",
        ],
        "note": "Часто B2B — нужен договор.",
    },
    {
        "id": "dataloop",
        "label": "Dataloop",
        "category": "labeling",
        "status_key": "DATALOOP_API_KEY",
        "env_var": "DATALOOP_API_KEY",
        "pay_hint": "пакеты аннотаций",
        "signup_url": "https://dataloop.ai/",
        "steps": [
            "Аккаунт dataloop.ai → Project → API key.",
            ".env.local: DATALOOP_API_KEY=...",
        ],
        "note": "Хорош для image + text labeling pipelines.",
    },
    {
        "id": "labelbox",
        "label": "Labelbox",
        "category": "labeling",
        "status_key": "LABELBOX_API_KEY",
        "env_var": "LABELBOX_API_KEY",
        "pay_hint": "экспорт размеченных датасетов",
        "signup_url": "https://labelbox.com/",
        "steps": [
            "labelbox.com → Settings → API keys.",
            ".env.local: LABELBOX_API_KEY=...",
        ],
        "note": "Экспорт в форматах для ML training.",
    },
]


def platform_status(env_var: str | None, status_key: str | None) -> tuple[str, str]:
    """Return (status, status_label) — active only if key present."""
    if not env_var and not status_key:
        return "active", "Работает"
    key = status_key or env_var
    if key and os.getenv(key, "").strip():
        return "active", "Ключ подключён"
    return "needs_key", "Нужен твой API-ключ"


def list_platforms() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in PLATFORM_REGISTRY:
        status, status_label = platform_status(p.get("env_var"), p.get("status_key"))
        item = dict(p)
        item["status"] = status
        item["status_label"] = status_label
        item["connected"] = status == "active"
        out.append(item)
    return out


def connected_count() -> int:
    return sum(1 for p in list_platforms() if p.get("connected"))


def ceo_checklist() -> list[dict[str, str]]:
    """What CEO must do — cannot be automated without keys."""
    platforms = list_platforms()
    pending = [p for p in platforms if not p.get("connected") and p.get("env_var")]
    steps: list[dict[str, str]] = [
        {
            "step": "1",
            "title": "Запусти ферму",
            "detail": "Genesis.exe → главная → «Запустить ферму». Внутренняя очередь уже зарабатывает копейки.",
        },
        {
            "step": "2",
            "title": "Подключи Groq (умная разметка)",
            "detail": "console.groq.com → ключ → .env.local: GENESIS_GROQ_API_KEY=gsk_... → перезапуск.",
        },
        {
            "step": "3",
            "title": "Подключи Google Places (больше сырья)",
            "detail": "Google Cloud → Places API → .env.local: GOOGLE_PLACES_API_KEY=AIza... → перезапуск.",
        },
    ]
    if pending:
        steps.append(
            {
                "step": "4",
                "title": f"Выбери биржу ({len(pending)} без ключа)",
                "detail": (
                    "Без твоего аккаунта Genesis не может получать € с Scale/Toloka/MTurk. "
                    "Зарегистрируйся на одной бирже ниже → вставь ключ в .env.local."
                ),
            }
        )
    else:
        steps.append(
            {
                "step": "4",
                "title": "Биржи подключены",
                "detail": "Комбайны могут сдавать разметку на внешние площадки.",
            }
        )
    steps.append(
        {
            "step": "5",
            "title": "Скачай экспорт разметки",
            "detail": "Кнопка «Скачать разметку» — файл для продажи или загрузки на биржу вручную.",
        }
    )
    return steps
