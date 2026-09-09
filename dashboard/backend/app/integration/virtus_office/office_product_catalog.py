"""Virtus Office commercial Product Catalog — SSOT for vitrine + ads.

Technical SKU ids stay internal. Public products map to executors.
UI / checkout must read live + price from here (and OFFICE_PRICE_MATRIX_EUR).

Rule: customer_sellable / buy only when executor+validator+E2E gates pass
and SKU is in OFFICE_SELLABLE_NOW (or free tool with no payment).
"""

from __future__ import annotations

from typing import Any

from app.integration.virtus_office.office_job_ssot import (
    OFFICE_PIPELINE_LIVE,
    OFFICE_PRICE_MATRIX_EUR,
    OFFICE_SELLABLE_NOW,
)

# Commercial product ids (public).
PRODUCT_PDF_PRO = "pdf_pro"
PRODUCT_CV_BEWERBUNG = "cv_bewerbung_pack"
PRODUCT_TRANSLATION = "translation_pack"
PRODUCT_SALES_KIT = "sales_kit"
PRODUCT_SMART = "smart"
PRODUCT_QR = "qr_code"

# Technical action ids used by job engine.
ACTION_PDF_PRO = "pdf_pro"
ACTION_TRANSLATION_PACK = "translation_pack"
ACTION_CV_PACK = "bewerbung_paket"  # existing executor — commercial alias
ACTION_QR = "qr_code"

OFFICE_PRODUCT_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": PRODUCT_SMART,
        "category": "entry",
        "name_en": "Smart Office",
        "price_eur": None,
        "purchase_type": "guided",
        "action_ids": [],
        "href": "/office/smart",
        "free": True,
        "customer_sellable": True,
        "payment_enabled": False,
        "delivery_enabled": False,
        "one_time": False,
        "output": ["recommendation"],
    },
    {
        "id": PRODUCT_PDF_PRO,
        "category": "personal",
        "name_en": "PDF PRO",
        "price_key": "pdf_pro",
        "price_eur": 29.90,
        "purchase_type": "one_time",
        "action_ids": [ACTION_PDF_PRO],
        "wraps": [
            "searchable_pdf",
            "redaction",
            "fillable_pdf",
            "pdf_a_2b",
            "document_archive",
            "document_quality_check",
        ],
        "href": "/office/pdf-pro",
        "free": False,
        "customer_sellable": True,
        "payment_enabled": True,
        "delivery_enabled": True,
        "one_time": True,
        "output": ["zip"],
    },
    {
        "id": PRODUCT_CV_BEWERBUNG,
        "category": "personal",
        "name_en": "CV & Bewerbung",
        "price_key": "large_pack",
        "price_eur": 24.90,
        "purchase_type": "one_time",
        "action_ids": [ACTION_CV_PACK],
        "wraps": [
            "lebenslauf_create",
            "lebenslauf_improve",
            "bewerbungsschreiben",
            "bewerbung_paket",
        ],
        "href": "/office/cv-bewerbung",
        "free": False,
        "customer_sellable": True,
        "payment_enabled": True,
        "delivery_enabled": True,
        "one_time": True,
        "output": ["pdf", "docx", "zip"],
    },
    {
        "id": PRODUCT_TRANSLATION,
        "category": "personal",
        "name_en": "Translation Pack",
        "price_key": "translation_pack",
        "price_eur": 19.90,
        "purchase_type": "one_time",
        "action_ids": [ACTION_TRANSLATION_PACK],
        "wraps": ["translate"],
        "href": "/office/translation-pack",
        "free": False,
        "customer_sellable": True,
        "payment_enabled": True,
        "delivery_enabled": True,
        "one_time": True,
        "output": ["pdf", "docx", "zip"],
    },
    {
        "id": PRODUCT_SALES_KIT,
        "category": "business",
        "name_en": "Sales Kit",
        "price_eur": 99.0,
        "price_from_eur": 99.0,
        "tiers": [
            {"action_id": "sales_kit_basic", "price_eur": 99.0},
            {"action_id": "sales_kit_business", "price_eur": 199.0},
            {"action_id": "sales_kit_professional", "price_eur": 299.0},
        ],
        "purchase_type": "one_time",
        "action_ids": [
            "sales_kit_basic",
            "sales_kit_business",
            "sales_kit_professional",
        ],
        "href": "/office/sales-kit",
        "free": False,
        "customer_sellable": True,
        "payment_enabled": True,
        "delivery_enabled": True,
        "one_time": True,
        "output": ["pdf", "docx", "zip"],
    },
    {
        "id": PRODUCT_QR,
        "category": "tools",
        "name_en": "QR Code",
        "price_eur": 0.0,
        "purchase_type": "free",
        "action_ids": [ACTION_QR],
        "href": "/office/qr",
        "free": True,
        "customer_sellable": True,
        "payment_enabled": False,
        "delivery_enabled": True,
        "one_time": False,
        "output": ["png", "svg", "pdf"],
    },
)


def _action_live(action_id: str) -> bool:
    if action_id == ACTION_QR:
        return True
    if not OFFICE_PIPELINE_LIVE:
        return False
    return action_id in OFFICE_SELLABLE_NOW


def catalog_public(*, include_blocked: bool = False) -> list[dict[str, Any]]:
    """Public-safe product list for /api/office/catalog and UI."""
    out: list[dict[str, Any]] = []
    sellable = set(OFFICE_SELLABLE_NOW)
    for row in OFFICE_PRODUCT_CATALOG:
        actions = list(row.get("action_ids") or [])
        if row["id"] == PRODUCT_SMART:
            live = True
            buy = False
        elif row.get("free"):
            live = True
            buy = False
        else:
            live = bool(actions) and all(a in sellable for a in actions)
            buy = bool(live and row.get("customer_sellable") and row.get("payment_enabled"))
        price = row.get("price_eur")
        pk = row.get("price_key")
        if pk and pk in OFFICE_PRICE_MATRIX_EUR:
            price = float(OFFICE_PRICE_MATRIX_EUR[pk])
        item = {
            "id": row["id"],
            "category": row["category"],
            "name_en": row["name_en"],
            "href": row["href"],
            "price_eur": price,
            "price_from_eur": row.get("price_from_eur", price),
            "purchase_type": row["purchase_type"],
            "one_time": bool(row.get("one_time")),
            "free": bool(row.get("free")),
            "live": live,
            "customer_sellable": bool(row.get("customer_sellable")),
            "payment_enabled": bool(buy),
            "delivery_enabled": bool(row.get("delivery_enabled")),
            "action_ids": actions,
            "wraps": list(row.get("wraps") or []),
            "output": list(row.get("output") or []),
            "tiers": list(row.get("tiers") or []),
        }
        if live or include_blocked:
            out.append(item)
    return out


def product_by_id(product_id: str) -> dict[str, Any] | None:
    pid = (product_id or "").strip().lower()
    for row in catalog_public(include_blocked=True):
        if row["id"] == pid:
            return row
    return None
