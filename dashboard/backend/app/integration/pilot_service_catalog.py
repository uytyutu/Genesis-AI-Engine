"""Pilot service catalog — expands offers without new Factory engines.

Checkout online today: Landing Path A only.
Pilot (mailto / CEO quote): audits, Site Boost, GMB, etc.
Horizon: listed for CEO planning, not sold as one-click.
"""

from __future__ import annotations

from typing import Any

# Spider / Desk signal → suggested service ids (recommendation only).
SPIDER_SIGNAL_TO_SERVICES: dict[str, tuple[str, ...]] = {
    "no_site": ("basic", "business", "premium"),
    "no_https": ("website_audit", "security_audit"),
    "no_whatsapp": ("site_boost",),
    "no_maps": ("site_boost",),
    "no_schema": ("seo_audit", "site_boost"),
    "poor_seo": ("seo_audit",),
    "slow_site": ("website_audit",),
    "no_google_business": ("google_business_setup",),
    "few_reviews": ("review_audit",),
    "outdated_design": ("business", "website_migration"),
}

_SUPPORT_MAIL = "hello@genesis-ai-engine.com"


def _mailto(subject: str) -> str:
    from urllib.parse import quote

    return f"mailto:{_SUPPORT_MAIL}?subject={quote(subject)}"


# Addon / audit SKUs for public + CEO catalog (not Stripe packages).
PILOT_CATALOG_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "site_boost",
        "name": "Site Boost",
        "name_ru": "Site Boost",
        "price_label": "ab 149 €",
        "timeline": "2–5 Tage",
        "includes": [
            "WhatsApp-Button",
            "Google Maps",
            "Formular / SEO-Basics",
            "Open Graph",
        ],
        "description": "Kein neuer Standort — gezielte Verbesserungen am bestehenden Auftritt (nach Zugang).",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage Site Boost"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["no_whatsapp", "no_maps", "no_schema"],
    },
    {
        "id": "website_audit",
        "name": "Website Audit",
        "name_ru": "Аудит сайта",
        "price_label": "ab 79 €",
        "timeline": "1–3 Tage",
        "includes": [
            "HTTPS / Mobile",
            "WhatsApp / Maps / SEO",
            "Schema / OG Check",
            "Kurzer Bericht + Angebot",
        ],
        "description": "Bericht statt Umbau — Grundlage für Boost oder Neustart.",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage Website Audit"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["no_https", "slow_site", "poor_seo"],
    },
    {
        "id": "seo_audit",
        "name": "SEO Audit",
        "name_ru": "SEO-Audit",
        "price_label": "ab 99 €",
        "timeline": "2–4 Tage",
        "includes": ["Title / Description / H1", "robots / sitemap", "Schema", "Empfehlungen"],
        "description": "Technisches SEO-Check mit priorisierter Liste.",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage SEO Audit"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["poor_seo", "no_schema"],
    },
    {
        "id": "google_business_setup",
        "name": "Google Business Setup",
        "name_ru": "Google Business",
        "price_label": "ab 129 €",
        "timeline": "3–7 Tage",
        "includes": ["Profil-Check", "Stunden / Fotos / Links", "Handlungsplan"],
        "description": "Sichtbarkeit vor Ort — Karte und Bewertungen.",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage Google Business"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["no_google_business"],
    },
    {
        "id": "website_migration",
        "name": "Website Migration",
        "name_ru": "Миграция сайта",
        "price_label": "ab 199 €",
        "timeline": "3–10 Tage",
        "includes": ["Inhalt übernehmen", "Neuer oder angepasster Auftritt", "Go-live-Hilfe"],
        "description": "Vom alten CMS zum modernen Neustart — ohne Reseller-Hosting.",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage Website Migration"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["outdated_design"],
    },
    {
        "id": "review_audit",
        "name": "Review Audit",
        "name_ru": "Аудит отзывов",
        "price_label": "ab 59 €",
        "timeline": "1–2 Tage",
        "includes": ["Google-Bewertungen", "Schnitt / Anzahl", "Empfehlungen"],
        "description": "Reputation kurz geprüft — Basis für nächste Schritte.",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage Review Audit"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["few_reviews"],
    },
    {
        "id": "security_audit",
        "name": "Security Audit (HTTPS)",
        "name_ru": "Security Audit",
        "price_label": "ab 69 €",
        "timeline": "1–3 Tage",
        "includes": ["HTTPS / Zertifikat", "Basis-Risiken", "Handlungsplan"],
        "description": "Kein Penetrationstest — praxisnaher Check für SMB.",
        "cta": "Anfrage senden",
        "cta_href": _mailto("Anfrage Security Audit"),
        "available": False,
        "tier": "pilot_quote",
        "spider_signals": ["no_https"],
    },
)

HORIZON_CATALOG_ITEMS: tuple[dict[str, Any], ...] = (
    {
        "id": "ai_audit",
        "name": "AI / Media Audit (Hive)",
        "price_label": "Horizon",
        "description": "Moderation, OCR, AI-Detection — nach Gate 1 + gültigem API-Key.",
        "cta": "Bald",
        "cta_href": "/services",
        "available": False,
        "tier": "horizon",
        "includes": [],
        "timeline": "—",
    },
    {
        "id": "brand_kit",
        "name": "Brand Kit",
        "price_label": "Horizon",
        "description": "Farben, Logo-Platz, Typo — nach erstem Kundenfeedback.",
        "cta": "Bald",
        "cta_href": "/services",
        "available": False,
        "tier": "horizon",
        "includes": [],
        "timeline": "—",
    },
    {
        "id": "social_audit",
        "name": "Social Audit",
        "price_label": "Horizon",
        "description": "Instagram / Facebook / LinkedIn — später.",
        "cta": "Bald",
        "cta_href": "/services",
        "available": False,
        "tier": "horizon",
        "includes": [],
        "timeline": "—",
    },
    {
        "id": "crm_starter",
        "name": "CRM Starter",
        "price_label": "Horizon",
        "description": "Formulare → Sheets / CRM — nach wiederholbarer Nachfrage.",
        "cta": "Bald",
        "cta_href": "/services",
        "available": False,
        "tier": "horizon",
        "includes": [],
        "timeline": "—",
    },
)


def signals_from_site_issues(issues: list[str] | None) -> list[str]:
    """Map human-readable site_analysis issues → spider signal keys."""
    found: list[str] = []
    seen: set[str] = set()
    for raw in issues or ():
        low = str(raw or "").lower()
        mapped: str | None = None
        if "https" in low or "unsicher" in low:
            mapped = "no_https"
        elif "whatsapp" in low or "wa.me" in low or "anruf" in low:
            mapped = "no_whatsapp"
        elif "seo" in low or "seitentitel" in low or "meta-tags" in low:
            mapped = "poor_seo"
        elif "langsam" in low or "ms)" in low:
            mapped = "slow_site"
        elif "veraltet" in low or "platzhalter" in low or "baustelle" in low:
            mapped = "outdated_design"
        elif "nicht erreichbar" in low:
            mapped = "no_site"
        if mapped and mapped not in seen:
            seen.add(mapped)
            found.append(mapped)
    return found


def suggest_services_for_signals(signals: list[str] | tuple[str, ...] | None) -> list[str]:
    """Map lead signals → service ids (deduped, order stable)."""
    out: list[str] = []
    seen: set[str] = set()
    for raw in signals or ():
        key = str(raw or "").strip().lower()
        for sid in SPIDER_SIGNAL_TO_SERVICES.get(key, ()):
            if sid not in seen:
                seen.add(sid)
                out.append(sid)
    return out


def suggest_services_for_site_issues(issues: list[str] | None) -> list[str]:
    return suggest_services_for_signals(signals_from_site_issues(issues))


def catalog_item_by_id(service_id: str) -> dict[str, Any] | None:
    sid = (service_id or "").strip()
    for row in (*PILOT_CATALOG_ITEMS, *HORIZON_CATALOG_ITEMS):
        if row["id"] == sid:
            return dict(row)
    return None


def public_pilot_categories() -> list[dict[str, Any]]:
    """Categories for /services pricing display."""

    def _item(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": row["id"],
            "name": row["name"],
            "price_label": row["price_label"],
            "timeline": row.get("timeline") or "—",
            "includes": list(row.get("includes") or [])[:6],
            "description": row.get("description") or "",
            "cta": row["cta"],
            "cta_href": row["cta_href"],
            "available": bool(row.get("available")),
            "tier": row.get("tier") or "horizon",
        }

    return [
        {
            "id": "path_a_pilot",
            "name": "Weitere Leistungen · auf Anfrage",
            "description": (
                "Verbesserungen und Checks für bestehende Auftritte — "
                "kurze Anfrage, persönliches Angebot."
            ),
            "items": [_item(r) for r in PILOT_CATALOG_ITEMS],
        },
        # Horizon NOT exposed on public storefront — CEO only via Desk.
    ]


FOCUS_NICHES_DE: tuple[dict[str, str], ...] = (
    {"id": "handwerk", "label": "Handwerk", "examples": "Elektriker, Sanitär, Heizung, Dach, Fliesen"},
    {"id": "repair", "label": "Reparatur", "examples": "Haushaltsgeräte, PC, Smartphone"},
    {"id": "auto", "label": "Auto", "examples": "Werkstatt, Reifen, Detailing"},
    {"id": "gesundheit", "label": "Gesundheit", "examples": "Zahnarzt, Physio, Praxis"},
    {"id": "beauty", "label": "Beauty", "examples": "Friseur, Barber, Kosmetik"},
    {"id": "dienstleistungen", "label": "Dienstleistungen", "examples": "Reinigung, Umzug, Garten, Möbel"},
    {"id": "professional", "label": "Professional Services", "examples": "Steuerberater, Anwalt, Buchhaltung"},
)

SIGNAL_OFFER_ROWS_DE: tuple[dict[str, str], ...] = (
    {"signal": "Kein Website", "offer": "Landing Basic / Business / Premium"},
    {"signal": "Veraltete Website", "offer": "Migration oder Neustart"},
    {"signal": "Kein HTTPS", "offer": "Website / Security Audit"},
    {"signal": "Kein WhatsApp", "offer": "Site Boost"},
    {"signal": "Kein Google Maps", "offer": "Site Boost"},
    {"signal": "Kein Google Business", "offer": "Google Business Setup"},
    {"signal": "Schwaches SEO", "offer": "SEO Audit"},
    {"signal": "Sehr langsam", "offer": "Website Audit"},
)


def ceo_catalog_snapshot() -> dict[str, Any]:
    return {
        "checkout_online": ["basic", "business", "premium"],
        "pilot_quote": [r["id"] for r in PILOT_CATALOG_ITEMS if r.get("tier") == "pilot_quote"],
        "horizon": [r["id"] for r in HORIZON_CATALOG_ITEMS],
        "spider_signal_map": {k: list(v) for k, v in SPIDER_SIGNAL_TO_SERVICES.items()},
        "note": "Only /order Landing packages are Stripe checkout. Quotes via email until productized.",
        "sales_modes": {
            "auto": "Landing Path A — /order → pay → Factory → ZIP",
            "expert": "Pilot Anfrage — CEO quote + human delivery",
        },
        "focus_niches_de": list(FOCUS_NICHES_DE),
        "offer_formula_de": (
            "Wir haben Ihre Website geprüft, konkrete Lücken gefunden "
            "und schlagen die passende Leistung vor."
        ),
    }


def public_go_to_market() -> dict[str, Any]:
    return {
        "levels": [
            {
                "id": "1",
                "title": "1 · Leistung",
                "body": "Fertige Website für Ihren Betrieb — klar und mobil.",
            },
            {
                "id": "2",
                "title": "2 · Für wen",
                "body": "Lokale Betriebe in Deutschland, die Anfragen online gewinnen wollen.",
            },
            {
                "id": "3",
                "title": "3 · Passgenau",
                "body": "Wir schauen, was fehlt — und schlagen die passende Lösung vor.",
            },
        ],
        "niches": [{"id": n["id"], "label": n["label"], "examples": n["examples"]} for n in FOCUS_NICHES_DE],
        "signals": list(SIGNAL_OFFER_ROWS_DE),
        "modes": {
            "auto": "Website online bestellen",
            "expert": "Weitere Leistungen auf Anfrage",
        },
        "horizon_after_pilot": {
            "id": "event_signals",
            "title": "Ereignisse statt nur Technik-Lücken",
            "examples": [
                "Neu eröffnet",
                "Umgezogen",
                "Leistungen erweitert",
                "Viele neue Bewertungen",
                "Rebrand / neuer Name",
            ],
            "note": "Erst nach Gate 1 + ersten zahlenden Kunden — sonst Feature-Creep.",
        },
    }
