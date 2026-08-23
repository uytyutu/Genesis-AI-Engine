"""Cinematic AI Experience — commercial product config (not Basic/Business/Premium)."""

from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONFIG_PATH = Path(__file__).with_name("products.json")

MEDIA_STATUSES = (
    "NOT_REQUESTED",
    "AWAITING_PAYMENT",
    "PAID",
    "READY_FOR_GENERATION",
    "GENERATING",
    "QA",
    "COMPLETED",
    "BUDGET_EXHAUSTED",
    "FAILED",
    "MANUAL_REVIEW",
)

DEFAULT_PRODUCT_ID = "cinematic_ai_experience"


@lru_cache(maxsize=1)
def _raw_config() -> dict[str, Any]:
    data = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"version": 1, "products": [], "providers": {}}
    return data


def reload_config() -> None:
    _raw_config.cache_clear()


def list_products() -> list[dict[str, Any]]:
    rows = _raw_config().get("products") or []
    return [deepcopy(r) for r in rows if isinstance(r, dict)]


def get_product(product_id: str | None = None) -> dict[str, Any] | None:
    pid = (product_id or DEFAULT_PRODUCT_ID).strip()
    for row in list_products():
        if str(row.get("product_id") or "") == pid:
            return row
        if str(row.get("shop_variant_product_id") or "") == pid:
            # Normalize shop variant into a product-shaped dict
            return {
                "product_id": row["shop_variant_product_id"],
                "name": f"{row.get('name')} (Shop)",
                "price_eur": float(row.get("shop_price_eur") or row.get("price_eur") or 0),
                "media_budget_eur": float(
                    row.get("shop_media_budget_eur") or row.get("media_budget_eur") or 0
                ),
                "status": row.get("status") or "available",
                "client_label_de": row.get("client_label_de"),
                "client_label_en": row.get("client_label_en"),
                "client_label_ru": row.get("client_label_ru"),
                "client_description_de": row.get("client_description_de"),
                "client_description_en": row.get("client_description_en"),
                "client_description_ru": row.get("client_description_ru"),
                "parent_product_id": row.get("product_id"),
            }
    return None


def provider_flags() -> dict[str, Any]:
    return deepcopy(_raw_config().get("providers") or {})


def client_facing_product(product_id: str | None = None, *, lang: str = "de") -> dict[str, Any]:
    """Public catalog card — never exposes media_budget_eur or provider costs."""
    row = get_product(product_id) or get_product(DEFAULT_PRODUCT_ID)
    if not row:
        return {"ok": False, "error": "product_missing"}
    lang_l = (lang or "de").lower()[:2]
    label = (
        row.get(f"client_label_{lang_l}")
        or row.get("client_label_en")
        or row.get("name")
    )
    desc = (
        row.get(f"client_description_{lang_l}")
        or row.get("client_description_en")
        or ""
    )
    return {
        "ok": True,
        "product_id": row["product_id"],
        "name": label,
        "description": desc,
        "price_eur": float(row.get("price_eur") or 0),
        "status": row.get("status") or "available",
        # Explicitly omit internal budget / margin / provider
    }
