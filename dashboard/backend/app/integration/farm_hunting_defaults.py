"""Default high-value hunting vector for Global Spider + farm filters."""

from __future__ import annotations

from typing import Any

HIGH_VALUE_SEED_TARGETS: list[str] = [
    "сравнение ответов чат-ботов",
    "проверка фактов в текстах",
    "определение тональности отзывов",
    "выявление спама в комментариях",
    "транскрибация речи из видео",
    "поиск ошибок в программном коде",
    "классификация новостей по темам",
    "контекстный анализ документов",
    "оценка безопасности контента",
    "сравнение качества текста",
    "анализ юридических документов",
    "сегментация медицинских снимков",
    "выделение объектов на видео",
]

HIGH_VALUE_TOLOKA_CATEGORIES: list[str] = [
    "LLM response comparison",
    "chatbot evaluation",
    "fact checking text",
    "sentiment analysis reviews",
    "spam detection comments",
    "content safety moderation",
    "document context analysis",
    "text quality comparison",
    "news topic classification",
    "code error detection",
    "video speech transcription",
    "autonomous driving object labeling",
    "road segmentation annotation",
    "medical image segmentation",
    "legal document review",
]

HIGH_VALUE_PLACES_QUERIES: list[str] = [
    "Anwaltskanzlei website",
    "medizinische Klinik website",
    "news portal website",
    "software development company website",
    "online shop customer reviews",
    "forum community website",
    "video production studio website",
    "autonomous driving research lab",
]

DEFAULT_MIN_TASK_PRICE = 0.02
DEFAULT_POLLING_INTERVAL_SEC = 8


def merge_hunting_config(cfg: dict[str, Any]) -> dict[str, Any]:
    out = dict(cfg)

    def _merge_list(key: str, defaults: list[str]) -> None:
        existing = [str(x).strip() for x in (out.get(key) or []) if str(x).strip()]
        seen = {x.casefold() for x in existing}
        for item in defaults:
            if item.casefold() not in seen:
                existing.append(item)
                seen.add(item.casefold())
        out[key] = existing

    _merge_list("seed_targets", HIGH_VALUE_SEED_TARGETS)
    _merge_list("toloka_task_categories", HIGH_VALUE_TOLOKA_CATEGORIES)
    _merge_list("places_queries", HIGH_VALUE_PLACES_QUERIES)

    if "min_task_price" not in out:
        out["min_task_price"] = DEFAULT_MIN_TASK_PRICE
    if "polling_interval_sec" not in out and "polling_interval" not in out:
        out["polling_interval_sec"] = DEFAULT_POLLING_INTERVAL_SEC
    elif "polling_interval_sec" not in out and "polling_interval" in out:
        out["polling_interval_sec"] = int(out["polling_interval"])

    return out


def hunting_settings(cfg: dict[str, Any]) -> dict[str, Any]:
    merged = merge_hunting_config(cfg)
    raw_min = merged.get("min_task_price", DEFAULT_MIN_TASK_PRICE)
    try:
        min_price = max(0.0, float(raw_min))
    except (TypeError, ValueError):
        min_price = DEFAULT_MIN_TASK_PRICE
    raw_poll = merged.get("polling_interval_sec") or merged.get("polling_interval") or DEFAULT_POLLING_INTERVAL_SEC
    try:
        poll = max(3, min(60, int(raw_poll)))
    except (TypeError, ValueError):
        poll = DEFAULT_POLLING_INTERVAL_SEC
    return {
        "min_task_price": round(min_price, 4),
        "polling_interval_sec": poll,
    }
