"""Service price list — editable without changing gateway logic.

Default prices live here; CEO may override via memory/commercial_api_pricing.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Defaults only — runtime overrides from JSON file (no redeploy for price change).
DEFAULT_PRICES_EUR: dict[str, float] = {
    "audit": 0.49,
    "leads": 0.80,
    "factory": 2.50,
}

PRICING_FILE = "commercial_api_pricing.json"

# Product roadmap (status only — not a promise of revenue)
API_ROADMAP: list[dict[str, str]] = [
    {"version": "v1", "product": "audit", "status": "live", "note_ru": "Анализ сайта"},
    {"version": "v2", "product": "leads", "status": "preview", "note_ru": "Поиск лидов"},
    {"version": "v3", "product": "factory", "status": "reserved", "note_ru": "Генерация лендингов"},
    {"version": "v4", "product": "agents", "status": "planned", "note_ru": "AI-агенты"},
    {"version": "v5", "product": "analytics", "status": "planned", "note_ru": "Аналитика и отчёты"},
]


def load_prices(memory_dir: Path | None = None) -> dict[str, float]:
    prices = dict(DEFAULT_PRICES_EUR)
    if memory_dir is None:
        return prices
    path = memory_dir / PRICING_FILE
    if not path.is_file():
        return prices
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return prices
    if not isinstance(raw, dict):
        return prices
    for key, val in raw.items():
        if key.startswith("_"):
            continue
        try:
            amount = float(val.get("price_eur") if isinstance(val, dict) else val)
        except (TypeError, ValueError, AttributeError):
            continue
        if amount >= 0:
            prices[str(key)] = round(amount, 4)
    return prices


def price_eur(product_id: str, memory_dir: Path | None = None) -> float:
    return float(load_prices(memory_dir).get(str(product_id), 0.0))


def pricing_public(memory_dir: Path | None = None) -> dict[str, Any]:
    prices = load_prices(memory_dir)
    methods = []
    for pid, amount in prices.items():
        methods.append(
            {
                "product": pid,
                "method": f"POST /api/v1/{pid}",
                "price_eur": amount,
                "currency": "EUR",
                "unit": "request" if pid != "factory" else "build",
            }
        )
    return {
        "currency": "EUR",
        "billing": "prepaid_balance_eur",
        "note_ru": (
            "Цены из каталога услуг. Файл commercial_api_pricing.json "
            "переопределяет defaults без изменения кода Gateway."
        ),
        "methods": methods,
        "roadmap": API_ROADMAP,
    }


def save_default_pricing_file(memory_dir: Path) -> Path:
    """Write starter override file if missing (CEO can edit)."""
    path = memory_dir / PRICING_FILE
    if path.is_file():
        return path
    payload = {
        "_comment": "Override product prices without code changes. Delete a key to use default.",
        **{k: {"price_eur": v} for k, v in DEFAULT_PRICES_EUR.items()},
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
