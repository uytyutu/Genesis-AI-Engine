"""R3.4.1 — Market Profile Layer (SSOT).

Single Source of Truth for market parameters.
R3.4.2.1: profiles are registered in MarketRegistry; resolve() reads the registry.

resolve(market_code) → MarketProfile
New country = register a profile — not if/else across Factory.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.factory.market_delivery import normalize_market

ENGINE_ID = "market_profile_v1"


@dataclass(frozen=True)
class MarketProfile:
    """Canonical market row — all Factory market params should flow from here."""

    market_code: str
    language: str
    currency: str
    locale: str
    phone_format: str
    address_format: str
    default_cta: str
    business_hours: str
    legal_footer_keys: tuple[str, ...]
    legal_page_slugs: tuple[str, ...]
    label: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# --- Seed profiles (registered into MarketRegistry below) ---

_SEED_PROFILES: tuple[MarketProfile, ...] = (
    MarketProfile(
        market_code="DE",
        label="Germany",
        language="de",
        currency="EUR",
        locale="de_DE",
        phone_format="+49",
        address_format="DE",
        default_cta="Termin buchen",
        business_hours="Mo–Fr",
        legal_footer_keys=("impressum", "datenschutz"),
        legal_page_slugs=("impressum.html", "datenschutz.html"),
    ),
    MarketProfile(
        market_code="GB",
        label="United Kingdom",
        language="en",
        currency="GBP",
        locale="en_GB",
        phone_format="+44",
        address_format="GB",
        default_cta="Book Now",
        business_hours="Mon–Fri",
        legal_footer_keys=("privacy", "contact"),
        legal_page_slugs=("privacy.html", "#contact"),
    ),
    MarketProfile(
        market_code="US",
        label="United States",
        language="en",
        currency="USD",
        locale="en_US",
        phone_format="+1",
        address_format="US",
        default_cta="Get Quote",
        business_hours="Mon–Fri",
        legal_footer_keys=("privacy", "terms"),
        legal_page_slugs=("privacy.html", "terms.html"),
    ),
    MarketProfile(
        market_code="UA",
        label="Ukraine",
        language="uk",
        currency="UAH",
        locale="uk_UA",
        phone_format="+380",
        address_format="UA",
        default_cta="Зв’язатися",
        business_hours="Пн–Пт",
        legal_footer_keys=("privacy", "contact"),
        legal_page_slugs=("privacy.html", "#contact"),
    ),
)


def _ensure_registry_seeded() -> None:
    """Idempotent seed into DEFAULT_REGISTRY (no behavior change for callers)."""
    from app.factory.market_registry import DEFAULT_REGISTRY

    if DEFAULT_REGISTRY.codes():
        return
    for profile in _SEED_PROFILES:
        DEFAULT_REGISTRY.register(profile)


def list_market_codes() -> tuple[str, ...]:
    """Ordered codes with explicit profiles (SSOT table)."""
    _ensure_registry_seeded()
    from app.factory.market_registry import DEFAULT_REGISTRY

    return DEFAULT_REGISTRY.codes()


def resolve(market_code: str | None) -> MarketProfile:
    """Return full MarketProfile for market_code via Market Registry.

    Unknown codes fall back to DE (same soft default as Path A today).
    Aliases: UK → GB via normalize_market.
    """
    _ensure_registry_seeded()
    from app.factory.market_registry import DEFAULT_REGISTRY

    return DEFAULT_REGISTRY.resolve(market_code)


def resolve_or_none(market_code: str | None) -> MarketProfile | None:
    """Strict lookup — None when no dedicated profile exists yet."""
    _ensure_registry_seeded()
    from app.factory.market_registry import DEFAULT_REGISTRY

    return DEFAULT_REGISTRY.get(market_code)


def coerce_market_profile(raw: MarketProfile | dict[str, Any] | None) -> MarketProfile | None:
    """Accept MarketProfile or CompositionResult.market_profile dict."""
    if raw is None:
        return None
    if isinstance(raw, MarketProfile):
        return raw
    if isinstance(raw, dict) and raw.get("legal_footer_keys") is not None:
        return MarketProfile(
            market_code=str(raw.get("market_code") or ""),
            language=str(raw.get("language") or "en"),
            currency=str(raw.get("currency") or ""),
            locale=str(raw.get("locale") or ""),
            phone_format=str(raw.get("phone_format") or ""),
            address_format=str(raw.get("address_format") or ""),
            default_cta=str(raw.get("default_cta") or ""),
            business_hours=str(raw.get("business_hours") or ""),
            legal_footer_keys=tuple(raw.get("legal_footer_keys") or ()),
            legal_page_slugs=tuple(raw.get("legal_page_slugs") or ()),
            label=str(raw.get("label") or ""),
        )
    return None


def html_lang_for_profile(profile: MarketProfile) -> str:
    """HTML lang attribute from profile — language field, not country if/else."""
    return (profile.language or "en").strip() or "en"


def profile_table() -> list[dict[str, str]]:
    """USER CAN VERIFY rows: Market · Language · Currency · CTA · Legal Keys."""
    _ensure_registry_seeded()
    from app.factory.market_registry import DEFAULT_REGISTRY

    return DEFAULT_REGISTRY.as_table()


def format_profile_table() -> str:
    rows = profile_table()
    headers = ("Market", "Language", "Currency", "CTA", "Legal Keys")
    keys = ("market", "language", "currency", "cta", "legal_keys")
    widths = [len(h) for h in headers]
    for row in rows:
        for i, k in enumerate(keys):
            widths[i] = max(widths[i], len(row[k]))
    line = "  ".join(h.ljust(widths[i]) for i, h in enumerate(headers))
    sep = "  ".join("-" * widths[i] for i in range(len(headers)))
    body = [
        "  ".join(row[k].ljust(widths[i]) for i, k in enumerate(keys)) for row in rows
    ]
    return "\n".join([line, sep, *body])


# Footer label catalog by language + legal key (not by country if/else).
_LEGAL_LABELS: dict[str, dict[str, str]] = {
    "de": {
        "impressum": "Impressum",
        "datenschutz": "Datenschutz",
        "privacy": "Datenschutz",
        "terms": "AGB",
        "contact": "Kontakt",
    },
    "en": {
        "impressum": "Legal notice",
        "datenschutz": "Privacy",
        "privacy": "Privacy",
        "terms": "Terms",
        "contact": "Contact",
    },
    "uk": {
        "impressum": "Правова інформація",
        "datenschutz": "Конфіденційність",
        "privacy": "Конфіденційність",
        "terms": "Умови",
        "contact": "Контакти",
    },
}


def legal_link_pairs(
    profile: MarketProfile,
) -> tuple[tuple[str, str], ...]:
    """(label, href) pairs for footer — driven only by MarketProfile fields."""
    labels = _LEGAL_LABELS.get(profile.language) or _LEGAL_LABELS["en"]
    keys = list(profile.legal_footer_keys)
    slugs = list(profile.legal_page_slugs)
    pairs: list[tuple[str, str]] = []
    for i, key in enumerate(keys):
        href = slugs[i] if i < len(slugs) else (slugs[-1] if slugs else "#")
        label = labels.get(key) or key.replace("_", " ").title()
        pairs.append((label, href))
    return tuple(pairs)


# Seed on import so resolve() works without an explicit bootstrap call.
_ensure_registry_seeded()
