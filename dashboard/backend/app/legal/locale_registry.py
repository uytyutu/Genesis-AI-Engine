"""Legal market registry — architecture for regional document variants (Horizon).

Not fully implemented: generators today default to DE/GDPR. This registry defines
how future markets map to document variants without changing product code.
"""

from __future__ import annotations

from typing import Any

# Canonical document slots (market-agnostic)
SLOT_IMPRESSUM = "impressum"
SLOT_PRIVACY = "privacy"
SLOT_TERMS = "terms"
SLOT_WITHDRAWAL = "withdrawal"
SLOT_COOKIES = "cookies"
SLOT_AI_DISCLAIMER = "ai_disclaimer"
SLOT_INTELLECTUAL_PROPERTY = "intellectual_property"

MARKET_DE = "DE"
MARKET_EU = "EU"
MARKET_PL = "PL"
MARKET_US_CA = "US-CA"

MARKET_LEGAL_PROFILES: dict[str, dict[str, Any]] = {
    MARKET_DE: {
        "label": "Deutschland",
        "privacy_framework": "GDPR",
        "impressum_required": True,
        "documents": {
            SLOT_IMPRESSUM: {"generator_id": "impressum", "locales": ["de"]},
            SLOT_PRIVACY: {"generator_id": "datenschutz", "locales": ["de"], "framework": "GDPR"},
            SLOT_TERMS: {"generator_id": "agb", "locales": ["de"]},
            SLOT_WITHDRAWAL: {"generator_id": "widerruf", "locales": ["de"]},
            SLOT_COOKIES: {"generator_id": "cookies", "locales": ["de"]},
            SLOT_AI_DISCLAIMER: {"generator_id": "ai_disclaimer", "locales": ["de", "ru"]},
            SLOT_INTELLECTUAL_PROPERTY: {"generator_id": "intellectual_property", "locales": ["de"]},
        },
    },
    MARKET_EU: {
        "label": "European Union",
        "privacy_framework": "GDPR",
        "impressum_required": False,
        "documents": {
            SLOT_PRIVACY: {"generator_id": "datenschutz", "locales": ["de", "en"], "framework": "GDPR"},
            SLOT_TERMS: {"generator_id": "agb", "locales": ["de", "en"]},
            SLOT_COOKIES: {"generator_id": "cookies", "locales": ["de", "en"]},
            SLOT_AI_DISCLAIMER: {"generator_id": "ai_disclaimer", "locales": ["de", "en"]},
        },
    },
    MARKET_PL: {
        "label": "Polska",
        "privacy_framework": "RODO",
        "impressum_required": False,
        "documents": {
            SLOT_PRIVACY: {"generator_id": "rodo", "locales": ["pl"], "framework": "RODO", "status": "horizon"},
            SLOT_TERMS: {"generator_id": "agb", "locales": ["pl"], "status": "horizon"},
        },
    },
    MARKET_US_CA: {
        "label": "California, USA",
        "privacy_framework": "CCPA",
        "impressum_required": False,
        "documents": {
            SLOT_PRIVACY: {"generator_id": "ccpa", "locales": ["en"], "framework": "CCPA", "status": "horizon"},
        },
    },
}

DEFAULT_MARKET = MARKET_DE


def list_market_profiles() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for code, profile in MARKET_LEGAL_PROFILES.items():
        docs = profile.get("documents") or {}
        out.append({
            "market_code": code,
            "label": profile["label"],
            "privacy_framework": profile.get("privacy_framework"),
            "impressum_required": profile.get("impressum_required", False),
            "document_slots": list(docs.keys()),
            "horizon_variants": [
                slot
                for slot, meta in docs.items()
                if isinstance(meta, dict) and meta.get("status") == "horizon"
            ],
        })
    return out


def resolve_generator_id(market_code: str, slot: str) -> str | None:
    profile = MARKET_LEGAL_PROFILES.get(market_code) or MARKET_LEGAL_PROFILES[DEFAULT_MARKET]
    doc = (profile.get("documents") or {}).get(slot)
    if not isinstance(doc, dict):
        return None
    return str(doc.get("generator_id") or "")


def localization_horizon_payload() -> dict[str, Any]:
    return {
        "status": "architecture_ready",
        "default_market": DEFAULT_MARKET,
        "markets": list_market_profiles(),
        "note": "Regional generators (RODO, CCPA, …) are registered but not implemented yet.",
    }
