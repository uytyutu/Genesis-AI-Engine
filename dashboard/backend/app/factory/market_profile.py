"""R3.4.1 — Market Profile Layer (SSOT).

Single Source of Truth for market parameters.
Factory migration to this module is R3.4.1.2+ / R3.4.2 — not this slice.

resolve(market_code) → MarketProfile
New country = new profile row here — not if/else across Factory.
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


# --- Canonical profiles (R3.4.1.1 minimum set) ---

_PROFILES: dict[str, MarketProfile] = {
    "DE": MarketProfile(
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
    "GB": MarketProfile(
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
    "US": MarketProfile(
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
    "UA": MarketProfile(
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
}


def list_market_codes() -> tuple[str, ...]:
    """Ordered codes with explicit profiles (SSOT table)."""
    return tuple(_PROFILES.keys())


def resolve(market_code: str | None) -> MarketProfile:
    """Return full MarketProfile for market_code.

    Unknown codes fall back to DE (same soft default as Path A today).
    Aliases: UK → GB via normalize_market.
    """
    code = normalize_market(market_code)
    if code in _PROFILES:
        return _PROFILES[code]
    return _PROFILES["DE"]


def resolve_or_none(market_code: str | None) -> MarketProfile | None:
    """Strict lookup — None when no dedicated profile exists yet."""
    code = normalize_market(market_code)
    return _PROFILES.get(code)


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
    rows: list[dict[str, str]] = []
    for code in list_market_codes():
        p = _PROFILES[code]
        rows.append(
            {
                "market": code,
                "language": p.language,
                "currency": p.currency,
                "cta": p.default_cta,
                "legal_keys": ", ".join(p.legal_footer_keys),
            }
        )
    return rows


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
