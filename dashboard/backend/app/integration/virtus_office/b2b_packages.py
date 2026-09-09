"""Virtus Office B2B high-value packages — catalog + readiness (honesty gate).

Binding:
  NO EXECUTOR → NO SKU on sellable vitrine
  NO VALIDATOR → NO HIGH-RISK SELL
  NO PASS → NO DELIVERY
  *_LIVE=false until Owner E2E PASS

These products MUST NOT enter OFFICE_SELLABLE_NOW while LIVE is false.
UI may show Coming Soon cards; never fake Buy / checkout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# Owner-approved LIVE flip (Sales Kit only).
SALES_KIT_LIVE = True
# Public buyer path (API + /office/sales-kit) may be ready while LIVE stays false.
SALES_KIT_PUBLIC_PATH_READY = True
COMPANY_PROFILE_LIVE = False
DOCUMENT_CLEANUP_LIVE = False
BUSINESS_TRANSLATION_LIVE = False
EXCEL_BUSINESS_LIVE = False
PROCESS_SOP_LIVE = False

# Canonical SKU ids (tiers for Sales Kit).
SALES_KIT_BASIC = "sales_kit_basic"
SALES_KIT_BUSINESS = "sales_kit_business"
SALES_KIT_PROFESSIONAL = "sales_kit_professional"
COMPANY_PROFILE = "company_profile"
DOCUMENT_CLEANUP_PACK = "document_cleanup_pack"
BUSINESS_TRANSLATION_PACK = "business_translation_pack"
EXCEL_BUSINESS_PACK = "excel_business_pack"
PROCESS_SOP_PACK = "process_sop_pack"

SALES_KIT_SKUS: frozenset[str] = frozenset(
    {SALES_KIT_BASIC, SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL}
)

B2B_PACKAGE_SKUS: frozenset[str] = frozenset(
    SALES_KIT_SKUS
    | {
        COMPANY_PROFILE,
        DOCUMENT_CLEANUP_PACK,
        BUSINESS_TRANSLATION_PACK,
        EXCEL_BUSINESS_PACK,
        PROCESS_SOP_PACK,
    }
)

# Initial target prices (EUR) — configuration only; not a LIVE claim.
B2B_PRICE_EUR: dict[str, float] = {
    SALES_KIT_BASIC: 99.0,
    SALES_KIT_BUSINESS: 199.0,
    SALES_KIT_PROFESSIONAL: 299.0,
    COMPANY_PROFILE: 149.0,
    DOCUMENT_CLEANUP_PACK: 99.0,
    BUSINESS_TRANSLATION_PACK: 99.0,
    EXCEL_BUSINESS_PACK: 149.0,
    PROCESS_SOP_PACK: 199.0,
}

# Document Cleanup Pack file-count tiers (config, not magic).
CLEANUP_TIER_LIMITS: dict[str, int] = {
    "basic": 3,
    "business": 10,
    "professional": 30,
}

B2B_DISCLAIMER_DE = (
    "Virtus Office erstellt Geschäftsdokumente nur aus Ihren bereitgestellten "
    "Informationen. Keine erfundenen Leistungen, Preise, Referenzen oder Garantien."
)

B2B_DISCLAIMER_EN = (
    "Virtus Office builds business documents only from your provided information. "
    "No invented services, prices, references, or guarantees."
)

# Product cards for status API / future LIVE vitrine (not sellable while LIVE=false).
B2B_PRODUCT_CARDS: tuple[dict[str, Any], ...] = (
    {
        "id": "sales_kit",
        "skus": [SALES_KIT_BASIC, SALES_KIT_BUSINESS, SALES_KIT_PROFESSIONAL],
        "live_flag": "SALES_KIT_LIVE",
        "priority": 1,
        "price_from_eur": 99.0,
        "label_de": "Sales Kit",
        "label_en": "Sales Kit",
        "subtitle_de": "Professionelle Vertriebsunterlagen aus Ihren Unternehmensdaten.",
        "subtitle_en": "Professional sales documents from your company materials.",
        "includes_de": [
            "Company Profile",
            "Angebot",
            "Preisübersicht",
            "E-Mail-Vorlage",
            "PDF/DOCX/ZIP je nach Tarif",
        ],
        "honesty_de": (
            "Nur auf Basis Ihrer bereitgestellten Informationen. "
            "Keine erfundenen Leistungen, Preise oder Referenzen."
        ),
    },
    {
        "id": "company_profile",
        "skus": [COMPANY_PROFILE],
        "live_flag": "COMPANY_PROFILE_LIVE",
        "priority": 2,
        "price_from_eur": 99.0,
        "label_de": "Company Profile",
        "label_en": "Company Profile",
        "subtitle_de": "Professioneller Unternehmensprofil-PDF/DOCX aus Ihren Materialien.",
        "subtitle_en": "Professional company profile PDF/DOCX from your materials.",
        "includes_de": ["Unternehmensprofil", "PDF", "DOCX"],
        "honesty_de": "Keine erfundenen Fakten über Ihr Unternehmen.",
    },
    {
        "id": "document_cleanup_pack",
        "skus": [DOCUMENT_CLEANUP_PACK],
        "live_flag": "DOCUMENT_CLEANUP_LIVE",
        "priority": 3,
        "price_from_eur": 99.0,
        "label_de": "Document Cleanup Pack",
        "label_en": "Document Cleanup Pack",
        "subtitle_de": "Dokumente vereinheitlichen und professionell aufbereiten.",
        "subtitle_en": "Standardize and professionally clean your document set.",
        "includes_de": ["Formatierung", "Struktur", "PDF/DOCX-Normalisierung"],
        "honesty_de": "Keine Rechts-/Compliance-Zertifizierung.",
    },
    {
        "id": "business_translation_pack",
        "skus": [BUSINESS_TRANSLATION_PACK],
        "live_flag": "BUSINESS_TRANSLATION_LIVE",
        "priority": 4,
        "price_from_eur": 79.0,
        "label_de": "Business Translation Pack",
        "label_en": "Business Translation Pack",
        "subtitle_de": "Geschäftsdokumente übersetzen — Zielsprache muss gewählt werden.",
        "subtitle_en": "Translate business documents — target language must be explicit.",
        "includes_de": ["Übersetzung", "Struktur", "PDF/DOCX-Paket"],
        "honesty_de": "Keine erfundenen Geschäftsangaben; Zahlen/Namen sorgfältig erhalten.",
    },
    {
        "id": "excel_business_pack",
        "skus": [EXCEL_BUSINESS_PACK],
        "live_flag": "EXCEL_BUSINESS_LIVE",
        "priority": 5,
        "price_from_eur": 149.0,
        "label_de": "Excel Business Pack",
        "label_en": "Excel Business Pack",
        "subtitle_de": "Chaotische Tabellen in eine nutzbare Arbeitsmappe bringen.",
        "subtitle_en": "Turn messy spreadsheets into a usable working workbook.",
        "includes_de": ["Bereinigung", "Struktur", "Formeln", "Summary"],
        "honesty_de": "Kein Advanced-BI; keine erfundenen Daten.",
    },
    {
        "id": "process_sop_pack",
        "skus": [PROCESS_SOP_PACK],
        "live_flag": "PROCESS_SOP_LIVE",
        "priority": 6,
        "price_from_eur": 199.0,
        "label_de": "Process / SOP Pack",
        "label_en": "Process / SOP Pack",
        "subtitle_de": "Ihre Abläufe als strukturierte Prozessdokumentation.",
        "subtitle_en": "Your workflows as structured process documentation.",
        "includes_de": ["Prozessstruktur", "Checklisten", "PDF/DOCX"],
        "honesty_de": (
            "Nur Dokumentstrukturierung — keine Rechts-, Steuer- oder ISO-Beratung."
        ),
    },
)

_INTENT_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "sales_kit",
        (
            "sales kit",
            "vertriebsunterlagen",
            "present my company to customers",
            "dokumente für kunden",
            "angebot und preisliste",
            "angebot + preis",
            "customer email template",
            "unterlagen für kunden schicken",
            "prepare documents to send clients",
        ),
    ),
    (
        "company_profile",
        (
            "company profile",
            "unternehmensprofil",
            "company presentation",
            "firmenprofil",
            "professional company presentation",
        ),
    ),
    (
        "document_cleanup_pack",
        (
            "clean them up",
            "document cleanup",
            "dokumente aufräumen",
            "inconsistent",
            "vereinheitlichen",
            "standardize documents",
        ),
    ),
    (
        "business_translation_pack",
        (
            "business documents translated",
            "geschäftsdokumente übersetzen",
            "translation pack",
            "übersetzungspaket",
            "translated into german",
            "ins deutsche übersetzen",
        ),
    ),
    (
        "excel_business_pack",
        (
            "clean this excel",
            "excel business",
            "tabelle bereinigen",
            "make it usable",
            "excel aufräumen",
            "workbook",
        ),
    ),
    (
        "process_sop_pack",
        (
            "sop",
            "process document",
            "prozessdokument",
            "workflow into",
            "ablauf dokumentieren",
            "process pack",
        ),
    ),
)


def live_flag_for_product(product_id: str) -> bool:
    mapping = {
        "sales_kit": SALES_KIT_LIVE,
        "company_profile": COMPANY_PROFILE_LIVE,
        "document_cleanup_pack": DOCUMENT_CLEANUP_LIVE,
        "business_translation_pack": BUSINESS_TRANSLATION_LIVE,
        "excel_business_pack": EXCEL_BUSINESS_LIVE,
        "process_sop_pack": PROCESS_SOP_LIVE,
    }
    return bool(mapping.get((product_id or "").strip().lower(), False))


def live_flag_for_sku(sku_id: str) -> bool:
    aid = (sku_id or "").strip().lower()
    if aid in SALES_KIT_SKUS:
        return SALES_KIT_LIVE
    if aid == COMPANY_PROFILE:
        return COMPANY_PROFILE_LIVE
    if aid == DOCUMENT_CLEANUP_PACK:
        return DOCUMENT_CLEANUP_LIVE
    if aid == BUSINESS_TRANSLATION_PACK:
        return BUSINESS_TRANSLATION_LIVE
    if aid == EXCEL_BUSINESS_PACK:
        return EXCEL_BUSINESS_LIVE
    if aid == PROCESS_SOP_PACK:
        return PROCESS_SOP_LIVE
    return False


def is_b2b_sku(sku_id: str) -> bool:
    return (sku_id or "").strip().lower() in B2B_PACKAGE_SKUS


def price_eur_for_sku(sku_id: str) -> float | None:
    return B2B_PRICE_EUR.get((sku_id or "").strip().lower())


def detect_b2b_intent(text: str) -> dict[str, Any] | None:
    """Map free-text to a B2B product card id. Does NOT authorize sale."""
    blob = (text or "").strip().lower()
    if not blob:
        return None
    for product_id, needles in _INTENT_PATTERNS:
        if any(n in blob for n in needles):
            live = live_flag_for_product(product_id)
            card = next((c for c in B2B_PRODUCT_CARDS if c["id"] == product_id), None)
            return {
                "product_id": product_id,
                "live": live,
                "sellable": False if not live else True,
                "message_de": (
                    None
                    if live
                    else "Dieses Produkt ist derzeit noch nicht verfügbar."
                ),
                "message_en": (
                    None if live else "This product is not available yet."
                ),
                "label_de": (card or {}).get("label_de"),
                "price_from_eur": (card or {}).get("price_from_eur"),
            }
    return None


def readiness_record() -> dict[str, Any]:
    """Owner-facing readiness — never auto-flip LIVE."""
    from app.integration.virtus_office import sku_sales_kit as sk

    sales_exec = bool(getattr(sk, "EXECUTOR_IMPLEMENTED", False))
    sales_val = bool(getattr(sk, "VALIDATOR_IMPLEMENTED", False))
    e2e_status = "PENDING"
    try:
        # Prefer last Owner E2E report if present under default runtime path
        report_paths = [
            Path(".runtime") / "office_sales_kit_owner_e2e" / "SALES_KIT_OWNER_E2E.json",
            Path("dashboard/backend/.runtime/office_sales_kit_owner_e2e")
            / "SALES_KIT_OWNER_E2E.json",
        ]
        for rp in report_paths:
            if rp.is_file():
                data = json.loads(rp.read_text(encoding="utf-8"))
                if data.get("OWNER_E2E") == "PASS":
                    e2e_status = "PASS"
                elif data.get("OWNER_E2E") == "FAIL":
                    e2e_status = "FAIL"
                break
    except Exception:  # noqa: BLE001
        e2e_status = "PENDING"

    return {
        "SALES_KIT": {
            "executor": "PASS" if sales_exec else "FAIL",
            "validator": "PASS" if sales_val else "FAIL",
            "e2e": e2e_status,
            "live": SALES_KIT_LIVE,
            "skus": list(SALES_KIT_SKUS),
        },
        "COMPANY_PROFILE": {
            "executor": "PENDING",
            "validator": "PENDING",
            "e2e": "PENDING",
            "live": COMPANY_PROFILE_LIVE,
            "skus": [COMPANY_PROFILE],
        },
        "DOCUMENT_CLEANUP": {
            "executor": "PENDING",
            "validator": "PENDING",
            "e2e": "PENDING",
            "live": DOCUMENT_CLEANUP_LIVE,
            "skus": [DOCUMENT_CLEANUP_PACK],
        },
        "BUSINESS_TRANSLATION": {
            "executor": "PENDING",
            "validator": "PENDING",
            "e2e": "PENDING",
            "live": BUSINESS_TRANSLATION_LIVE,
            "skus": [BUSINESS_TRANSLATION_PACK],
            "note": "Reuse existing translate executor when LIVE; pack wrapper not sellable yet.",
        },
        "EXCEL_BUSINESS": {
            "executor": "PENDING",
            "validator": "PENDING",
            "e2e": "PENDING",
            "live": EXCEL_BUSINESS_LIVE,
            "skus": [EXCEL_BUSINESS_PACK],
        },
        "PROCESS_SOP": {
            "executor": "PENDING",
            "validator": "PENDING",
            "e2e": "PENDING",
            "live": PROCESS_SOP_LIVE,
            "skus": [PROCESS_SOP_PACK],
        },
    }


def public_coming_soon_cards() -> list[dict[str, Any]]:
    """Cards safe for Office UI Coming Soon section (no checkout)."""
    out: list[dict[str, Any]] = []
    for card in B2B_PRODUCT_CARDS:
        live = live_flag_for_product(str(card["id"]))
        out.append(
            {
                **card,
                "live": live,
                "cta": "start" if live else "coming_soon",
                "checkout_allowed": False if not live else True,
            }
        )
    return out


def sales_kit_sandbox_e2e_allowed() -> bool:
    """Controlled sandbox Payment E2E only — not a public LIVE flip."""
    import os

    return (os.environ.get("GENESIS_OFFICE_SALES_KIT_SANDBOX_E2E") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def assert_sales_kit_checkout_allowed(job: dict[str, Any], action_id: str) -> None:
    """Public purchase blocked while LIVE=false; sandbox E2E jobs may proceed."""
    from app.integration.virtus_office.job_engine import OfficeJobError

    aid = (action_id or "").strip().lower()
    if aid not in SALES_KIT_SKUS:
        return
    if live_flag_for_sku(aid):
        return
    if job.get("sales_kit_sandbox_e2e") and sales_kit_sandbox_e2e_allowed():
        return
    raise OfficeJobError(
        "product_not_live",
        "Sales Kit ist derzeit nicht verfügbar (LIVE=false).",
    )


def assert_not_in_sellable(sellable: tuple[str, ...] | frozenset[str] | set[str]) -> list[str]:
    """Return B2B SKUs wrongly listed as sellable while LIVE=false."""
    bad: list[str] = []
    for sku in B2B_PACKAGE_SKUS:
        if sku in sellable and not live_flag_for_sku(sku):
            bad.append(sku)
    return bad
