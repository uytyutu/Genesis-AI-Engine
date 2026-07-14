"""Genesis Production Platform — Product Catalog, Cost Engine, Auto Quote, B2B brief.

Конвейер = константа. Toloka = адаптер crash-test. B2B = прямой выход.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Internal unit costs (EUR) — from combiner economics + LLM estimate
_UNIT_COST_EUR: dict[str, float] = {
    "document_labeling": 0.018,
    "ocr_page": 0.022,
    "product_categorization": 0.008,
    "data_quality_check": 0.006,
    "translation_qa": 0.012,
    "text_classification": 0.015,
    "data_cleaning": 0.010,
}

# B2B sell price — margin ~3–5× cost (CEO tunable later)
_MARGIN_MULTIPLIER = 3.5

PRODUCT_CATALOG: list[dict[str, Any]] = [
    {
        "id": "svc_document_labeling",
        "service_number": 1,
        "title_ru": "Разметка документов",
        "problem_ru": "Хаос в PDF/сканах — нужна структура для ML или отчётов",
        "deliverables_ru": ["JSON", "CSV", "отчёт качества"],
        "unit": "страница",
        "unit_label_ru": "€/страница",
        "price_b2b_eur": 0.07,
        "cost_internal_eur": _UNIT_COST_EUR["document_labeling"],
        "sla_example_ru": "100 000 стр. → ~24–48 ч (зависит от сложности)",
        "capability_ids": ["labeling", "pdf_analysis", "data_cleaning"],
    },
    {
        "id": "svc_ocr",
        "service_number": 2,
        "title_ru": "OCR + структурирование",
        "problem_ru": "Бумага и сканы не попадают в систему",
        "deliverables_ru": ["текст", "поля", "CSV"],
        "unit": "страница",
        "unit_label_ru": "€/страница",
        "price_b2b_eur": 0.05,
        "cost_internal_eur": _UNIT_COST_EUR["ocr_page"],
        "sla_example_ru": "10 000 стр. → ~4–8 ч",
        "capability_ids": ["ocr", "pdf_analysis", "labeling"],
    },
    {
        "id": "svc_catalog",
        "service_number": 3,
        "title_ru": "Категоризация товаров",
        "problem_ru": "Каталог с ошибками, дубликатами, пустыми описаниями",
        "deliverables_ru": ["категории", "описания", "исправления"],
        "unit": "10 000 SKU",
        "unit_label_ru": "€ / 10k товаров",
        "price_b2b_eur": 100.0,
        "cost_internal_eur": _UNIT_COST_EUR["product_categorization"] * 10_000,
        "sla_example_ru": "50 000 SKU → ~2–6 ч",
        "capability_ids": ["classification", "data_cleaning", "labeling"],
    },
    {
        "id": "svc_data_qa",
        "service_number": 4,
        "title_ru": "Проверка качества данных",
        "problem_ru": "50k записей — где дубли, null, мусор?",
        "deliverables_ru": ["отчёт QA", "исправленный датасет", "JSON"],
        "unit": "1 000 записей",
        "unit_label_ru": "€ / 1k записей",
        "price_b2b_eur": 6.0,
        "cost_internal_eur": _UNIT_COST_EUR["data_quality_check"] * 1_000,
        "sla_example_ru": "50 000 записей → ~1–3 ч",
        "capability_ids": ["data_cleaning", "classification", "labeling"],
    },
    {
        "id": "svc_translation_qa",
        "service_number": 5,
        "title_ru": "Translation QA",
        "problem_ru": "Переводы нужно проверить на смысл и тон",
        "deliverables_ru": ["оценки", "правки", "CSV"],
        "unit": "1 000 слов",
        "unit_label_ru": "€ / 1k слов",
        "price_b2b_eur": 8.0,
        "cost_internal_eur": _UNIT_COST_EUR["translation_qa"] * 1_000,
        "sla_example_ru": "100k слов → ~4–12 ч",
        "capability_ids": ["labeling", "classification"],
    },
]

CAPABILITY_MARKETPLACE: list[dict[str, Any]] = [
    {"id": "ocr", "label_ru": "OCR", "ready": True, "combiner": "ai_labeling"},
    {"id": "labeling", "label_ru": "Labeling", "ready": True, "combiner": "ai_labeling"},
    {"id": "pdf_analysis", "label_ru": "PDF Analysis", "ready": True, "combiner": "ai_labeling"},
    {"id": "data_cleaning", "label_ru": "Data Cleaning", "ready": True, "combiner": "data_clean"},
    {"id": "classification", "label_ru": "Classification", "ready": True, "combiner": "text_classify"},
    {"id": "translation_qa", "label_ru": "Translation QA", "ready": True, "combiner": "ai_labeling"},
    {"id": "record_verify", "label_ru": "Record verify", "ready": True, "combiner": "record_verify"},
    {"id": "b2b_export", "label_ru": "B2B Export (JSON/CSV/API)", "ready": True, "combiner": "export"},
]

REVENUE_ROUTER_CHANNELS: list[dict[str, Any]] = [
    {
        "id": "b2b_direct",
        "label_ru": "Собственные B2B клиенты",
        "potential": "very_high",
        "potential_ru": "очень высокий",
        "margin_ru": "~100% выручки",
        "why_ru": "Прямой контракт · конвейер уже работает · без посредника",
        "status": "recommended_after_toloka_verdict",
    },
    {
        "id": "toloka",
        "label_ru": "Toloka",
        "potential": "low",
        "potential_ru": "низкий",
        "margin_ru": "микрозадачи · requester model",
        "why_ru": "Crash-test прочности · не стратегический центр",
        "status": "crash_test",
    },
    {
        "id": "clickworker",
        "label_ru": "Clickworker",
        "potential": "medium",
        "potential_ru": "средний",
        "margin_ru": "посредник",
        "why_ru": "Адаптер не подключён · анализ only",
        "status": "horizon",
    },
    {
        "id": "upwork",
        "label_ru": "Upwork / Freelance",
        "potential": "high",
        "potential_ru": "высокий",
        "margin_ru": "черновик + CEO approve",
        "why_ru": "Проекты · не автозаявки (ToS)",
        "status": "horizon",
    },
    {
        "id": "scale",
        "label_ru": "Scale AI",
        "potential": "medium",
        "potential_ru": "средний",
        "margin_ru": "enterprise gate",
        "why_ru": "Адаптер в registry · нужен аккаунт",
        "status": "adapter_ready",
    },
]

B2B_BRIEF_RU: dict[str, Any] = {
    "title": "Genesis Production Platform",
    "tagline_ru": "Платформа обработки данных под ключ — не «ИИ-бот», а готовый результат",
    "we_sell_ru": [
        "Скорость — часы, не недели",
        "Качество — Truth Engine + Auditor (Error Ledger)",
        "Автоматизацию рутины — ваши люди не размечают вручную",
    ],
    "problems_we_solve_ru": [
        "100 000 документов → структурированные JSON/CSV + отчёт за сутки",
        "Каталог товаров → категории, описания, исправления за часы",
        "50 000 записей → автоматическая проверка качества",
    ],
    "pitch_ru": (
        "Вы приносите данные (PDF, CSV, API). Мы возвращаем готовый результат "
        "с фиксированной ценой и сроком — до начала работы. Без Toloka, без бирж, "
        "без «чата с ИИ»."
    ),
    "packages_ru": [
        {
            "scenario": "Вариант 1",
            "client_says": "У нас 100 000 документов",
            "genesis_says": "Через 24–48 ч: структурированные данные, CSV, JSON, отчёт QA",
        },
        {
            "scenario": "Вариант 2",
            "client_says": "У нас каталог товаров",
            "genesis_says": "Через 2–6 ч: категории, описания, исправленные ошибки",
        },
        {
            "scenario": "Вариант 3",
            "client_says": "Проверить 50 000 записей",
            "genesis_says": "Автоматически: QA-отчёт + чистый датасет за 1–3 ч",
        },
    ],
    "cta_ru": "Загрузите файл или укажите объём — получите счёт и срок до старта работ.",
}

# Throughput: pages/records per worker-hour (conservative)
_THROUGHPUT_PER_HOUR: dict[str, float] = {
    "svc_document_labeling": 4_000,
    "svc_ocr": 3_000,
    "svc_catalog": 25_000,
    "svc_data_qa": 30_000,
    "svc_translation_qa": 20_000,
}


def _service_by_id(service_id: str) -> dict[str, Any] | None:
    for s in PRODUCT_CATALOG:
        if s["id"] == service_id:
            return s
    return None


def cost_engine_quote(
    *,
    service_id: str,
    volume: float,
    workers: int = 10,
) -> dict[str, Any]:
    """Cost Engine: внутренняя себестоимость, цена B2B, время."""
    svc = _service_by_id(service_id)
    if not svc:
        return {"ok": False, "message": f"Unknown service: {service_id}"}

    vol = max(1.0, float(volume))
    unit_cost = float(svc["cost_internal_eur"])
    if svc["id"] == "svc_catalog":
        internal_cost = unit_cost * (vol / 10_000)
        sell = float(svc["price_b2b_eur"]) * (vol / 10_000)
    elif svc["id"] == "svc_data_qa":
        internal_cost = unit_cost * (vol / 1_000)
        sell = float(svc["price_b2b_eur"]) * (vol / 1_000)
    elif svc["id"] == "svc_translation_qa":
        internal_cost = unit_cost * (vol / 1_000)
        sell = float(svc["price_b2b_eur"]) * (vol / 1_000)
    else:
        internal_cost = round(unit_cost * vol, 2)
        sell = round(float(svc["price_b2b_eur"]) * vol, 2)

    throughput = _THROUGHPUT_PER_HOUR.get(svc["id"], 5_000)
    hours = max(0.25, vol / (throughput * max(1, workers) / 10))
    minutes = int(round(hours * 60))

    margin_eur = round(sell - internal_cost, 2)
    margin_pct = round((margin_eur / sell) * 100, 1) if sell > 0 else 0

    return {
        "ok": True,
        "service_id": service_id,
        "service_title_ru": svc["title_ru"],
        "volume": vol,
        "volume_unit_ru": svc["unit"],
        "duration_minutes": minutes,
        "duration_label_ru": f"{minutes // 60} ч {minutes % 60} мин" if minutes >= 60 else f"{minutes} мин",
        "internal_cost_eur": round(internal_cost, 2),
        "sell_price_eur": round(sell, 2),
        "margin_eur": margin_eur,
        "margin_pct": margin_pct,
        "workers_assumed": workers,
        "deliverables_ru": svc["deliverables_ru"],
        "summary_ru": (
            f"{svc['title_ru']} · объём {vol:,.0f} {svc['unit']} · "
            f"срок ~{minutes} мин · себестоимость {internal_cost:.2f} € · "
            f"продать {sell:.2f} € · маржа {margin_pct}%"
        ),
        "truth_note_ru": "ESTIMATE — Auto Quote до подписания договора",
    }


def auto_quote_from_rows(*, row_count: int, service_id: str = "svc_data_qa", workers: int = 10) -> dict[str, Any]:
    """Клиент загрузил файл — оценка по числу строк."""
    q = cost_engine_quote(service_id=service_id, volume=float(row_count), workers=workers)
    if not q.get("ok"):
        return q
    return {
        **q,
        "quote_type": "auto_quote",
        "input_ru": f"Файл · {row_count:,} строк",
        "invoice_line_ru": f"Объём {row_count:,} · Стоимость {q['sell_price_eur']:.2f} € · Срок {q['duration_label_ru']}",
        "cta_ru": "Подтвердите заказ — конвейер запустится с тем же Workers/Export, выход B2B JSON/CSV",
    }


def build_production_platform(
    *,
    farm_state: dict[str, Any] | None = None,
    toloka_verdict: str = "",
) -> dict[str, Any]:
    """Full Production Platform bundle for API + UI."""
    state = farm_state or {}
    labels = int(state.get("labels_export_count") or 0)
    return {
        "platform_id": "genesis_production_platform",
        "title_ru": "Genesis Production Platform",
        "subtitle_ru": "Цифровая фабрика результатов — Toloka только crash-test",
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "conveyor_status_ru": (
            "Конвейер работает" if labels > 0 else "Ожидает сырья (Spider seeds в app/memory)"
        ),
        "toloka_role_ru": "Crash-test прочности · не центр стратегии",
        "toloka_verdict_hint_ru": toloka_verdict or "Ждём Wallet/Pipeline вердикт",
        "product_catalog": PRODUCT_CATALOG,
        "capability_marketplace": CAPABILITY_MARKETPLACE,
        "revenue_router": {
            "title_ru": "Revenue Router — куда выгоднее сегодня",
            "note_ru": "Read-only рейтинг · без автозаявок · CEO решает",
            "channels": REVENUE_ROUTER_CHANNELS,
            "recommended_ru": "B2B direct после Toloka вердикта «0» на wallet",
        },
        "b2b_brief": B2B_BRIEF_RU,
        "digital_workforce_ru": [
            {"role": "Scout", "module": "Global Spider"},
            {"role": "Analyst", "module": "Finance Guard + Cost Engine"},
            {"role": "Worker", "module": "Labeling Swarm"},
            {"role": "Auditor", "module": "Truth Engine + Error Ledger"},
            {"role": "Finance", "module": "cost_per_verified_eur"},
            {"role": "CEO", "module": "VRE + NOT VERIFIED"},
        ],
        "five_year_vision_ru": (
            "Клиент → загрузка → оценка → цена → выполнение → QA → счёт → оплата"
        ),
    }
