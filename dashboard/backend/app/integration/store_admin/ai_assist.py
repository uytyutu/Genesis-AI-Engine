"""Vector-style product copy assist for Store Admin (offline-safe baseline)."""

from __future__ import annotations

import re
from typing import Any


def _slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return (s or "product")[:80]


def _split_hint(hint: str) -> tuple[str, list[str]]:
    raw = re.sub(r"\s+", " ", (hint or "").strip())
    if not raw:
        return "New product", []
    parts = [p.strip() for p in re.split(r"[,;/|]", raw) if p.strip()]
    title = parts[0][:80] if parts else raw[:80]
    tags = parts[1:] if len(parts) > 1 else []
    return title, tags


def generate_product_fields(
    *,
    hint: str,
    store_name: str = "",
    store_category: str = "",
    language: str = "en",
    product_type: str = "physical",
) -> dict[str, Any]:
    """Heuristic AI assist — always works offline; ready for LLM swap later."""
    title, tags = _split_hint(hint)
    lang = (language or "en").lower()[:2]
    store = (store_name or "your shop").strip()
    category = (store_category or (tags[0] if tags else "General")).strip()
    brand = store

    if lang == "de":
        short = f"{title} — hochwertig und bereit für Ihren Shop {store}."
        description = (
            f"{title} ist ein sorgfältig ausgewähltes Angebot für {store}. "
            f"Ideal für Kundinnen und Kunden, die Qualität und klare Details erwarten. "
            f"Kategorie: {category}."
            + (f" Merkmale: {', '.join(tags)}." if tags else "")
        )
        seo_title = f"{title} | {store}"
        seo_desc = f"Entdecken Sie {title} bei {store}. {short}"[:155]
        size = ["S", "M", "L", "XL"]
        color = ["Schwarz", "Natur", "Blau"]
        material = ["Premium"]
    elif lang == "ru":
        short = f"{title} — для витрины {store}."
        description = (
            f"{title} — товар для магазина {store}. "
            f"Категория: {category}."
            + (f" Особенности: {', '.join(tags)}." if tags else "")
        )
        seo_title = f"{title} | {store}"
        seo_desc = f"{title} в магазине {store}. {short}"[:155]
        size = ["S", "M", "L", "XL"]
        color = ["Чёрный", "Бежевый", "Синий"]
        material = ["Premium"]
    else:
        short = f"{title} — ready for {store}."
        description = (
            f"{title} is curated for {store}. "
            f"Clear details, honest positioning, and a product page buyers trust. "
            f"Category: {category}."
            + (f" Highlights: {', '.join(tags)}." if tags else "")
        )
        seo_title = f"{title} | {store}"
        seo_desc = f"Shop {title} at {store}. {short}"[:155]
        size = ["S", "M", "L", "XL"]
        color = ["Black", "Natural", "Blue"]
        material = ["Premium"]

    variants: dict[str, Any] = {
        "size": size if product_type == "physical" else [],
        "color": color if product_type == "physical" else [],
        "material": material if product_type == "physical" else [],
        "weight": "0.5 kg" if product_type == "physical" else None,
    }

    return {
        "ok": True,
        "source": "vector_assist_v1",
        "product_type": product_type if product_type else "physical",
        "title": title,
        "short_description": short[:180],
        "description": description,
        "category": category[:60],
        "subcategory": (tags[1] if len(tags) > 1 else "")[:60],
        "brand": brand[:60],
        "variants": variants,
        "seo": {
            "title": seo_title[:70],
            "description": seo_desc,
            "slug": _slugify(title),
        },
        "suggested_sku": f"SKU-{_slugify(title)[:12].upper().replace('-', '')}",
        "note": "Offline assist — replaceable by live Vector LLM later without schema change.",
    }
