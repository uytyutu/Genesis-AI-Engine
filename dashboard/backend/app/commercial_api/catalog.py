"""Sellable Virtus API products — metadata; prices come from pricing.py."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.commercial_api.pricing import API_ROADMAP, load_prices

PRODUCTS_META: dict[str, dict[str, Any]] = {
    "audit": {
        "id": "audit",
        "path": "POST /api/v1/audit",
        "type": "Merchant",
        "title_ru": "Анализ сайта",
        "title_en": "Website audit",
        "description_ru": (
            "Клиент отправляет URL → Virtus возвращает JSON-отчёт. "
            "Оплата с баланса API-ключа. Ядро фермы скрыто."
        ),
        "unit": "request",
        "status": "live",
        "scope": "audit",
        "automation_score": 100,
    },
    "leads": {
        "id": "leads",
        "path": "POST /api/v1/leads",
        "type": "Merchant",
        "title_ru": "Выборка лидов (город / ниша)",
        "title_en": "Lead pack query",
        "description_ru": (
            "Зарезервировано: внешний доступ к Lead Farm. "
            "Preview без списания, пока не включён биллинг."
        ),
        "unit": "pack",
        "status": "preview",
        "scope": "leads",
        "automation_score": 80,
    },
    "factory": {
        "id": "factory",
        "path": "POST /api/v1/factory",
        "type": "Merchant",
        "title_ru": "Factory лендинг (ZIP)",
        "title_en": "Landing factory ZIP",
        "description_ru": "Зарезервировано: генерация пакета через Factory.",
        "unit": "build",
        "status": "reserved",
        "scope": "factory",
        "automation_score": 70,
    },
}


def catalog(memory_dir: Path | None = None) -> dict[str, Any]:
    prices = load_prices(memory_dir)
    products = []
    for meta in PRODUCTS_META.values():
        row = dict(meta)
        row["price_eur"] = prices.get(meta["id"], 0.0)
        products.append(row)
    return {
        "engine": "commercial_api_v0",
        "model_ru": (
            "Клиенты платят Virtus за инфраструктуру (API + интеллект), "
            "а не Virtus ищет центы на биржах. Owner Gate: ключи выдаёт CEO."
        ),
        "billing": "prepaid_balance_eur",
        "security_ru": (
            "Ключ → тариф/scope → rate limit → безопасный модуль → ответ. "
            "Ядро и ферма недоступны клиенту. Ключ можно отозвать."
        ),
        "products": products,
        "roadmap": API_ROADMAP,
        "auth": "Header X-API-Key: vc_...",
        "pricing_url": "/api/v1/pricing",
        "owner_gate_ru": (
            "Ключи создаёт только владелец (CEO). Virtus не регистрирует клиентов сама."
        ),
    }


def product(product_id: str, memory_dir: Path | None = None) -> dict[str, Any] | None:
    meta = PRODUCTS_META.get(str(product_id or "").strip())
    if not meta:
        return None
    row = dict(meta)
    row["price_eur"] = load_prices(memory_dir).get(meta["id"], 0.0)
    return row
