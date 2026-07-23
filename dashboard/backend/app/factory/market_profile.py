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
    # R3.4.2.3 — expansion via Registry only (no Factory logic changes)
    MarketProfile(
        market_code="FR",
        label="France",
        language="fr",
        currency="EUR",
        locale="fr_FR",
        phone_format="+33",
        address_format="FR",
        default_cta="Prendre rendez-vous",
        business_hours="Lun–Ven",
        legal_footer_keys=("mentions_legales", "confidentialite"),
        legal_page_slugs=("mentions-legales.html", "confidentialite.html"),
    ),
    MarketProfile(
        market_code="NL",
        label="Netherlands",
        language="nl",
        currency="EUR",
        locale="nl_NL",
        phone_format="+31",
        address_format="NL",
        default_cta="Afspraak maken",
        business_hours="Ma–Vr",
        legal_footer_keys=("privacy", "contact"),
        legal_page_slugs=("privacy.html", "#contact"),
    ),
    MarketProfile(
        market_code="AT",
        label="Austria",
        language="de",
        currency="EUR",
        locale="de_AT",
        phone_format="+43",
        address_format="AT",
        default_cta="Termin buchen",
        business_hours="Mo–Fr",
        legal_footer_keys=("impressum", "datenschutz"),
        legal_page_slugs=("impressum.html", "datenschutz.html"),
    ),
    MarketProfile(
        market_code="ES",
        label="Spain",
        language="es",
        currency="EUR",
        locale="es_ES",
        phone_format="+34",
        address_format="ES",
        default_cta="Pedir cita",
        business_hours="Lun–Vie",
        legal_footer_keys=("aviso_legal", "privacidad"),
        legal_page_slugs=("aviso-legal.html", "privacidad.html"),
    ),
    # Path A delivery markets — must not soft-fall back to DE (C remediation).
    MarketProfile(
        market_code="PL",
        label="Poland",
        language="pl",
        currency="PLN",
        locale="pl_PL",
        phone_format="+48",
        address_format="PL",
        default_cta="Umów wizytę",
        business_hours="Pn–Pt",
        legal_footer_keys=("privacy", "contact"),
        legal_page_slugs=("LEGAL_NOTICE.txt", "#contact"),
    ),
    MarketProfile(
        market_code="RU",
        label="Russia",
        language="ru",
        currency="EUR",
        locale="ru_RU",
        phone_format="+7",
        address_format="RU",
        default_cta="Отправить",
        business_hours="Пн–Пт",
        legal_footer_keys=("privacy", "contact"),
        legal_page_slugs=("LEGAL_NOTICE.txt", "#contact"),
    ),
)


def _ensure_registry_seeded() -> None:
    """Idempotent seed into DEFAULT_REGISTRY (register/overwrite seed rows)."""
    from app.factory.market_registry import DEFAULT_REGISTRY

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
    "fr": {
        "mentions_legales": "Mentions légales",
        "confidentialite": "Confidentialité",
        "privacy": "Confidentialité",
        "terms": "Conditions",
        "contact": "Contact",
    },
    "nl": {
        "privacy": "Privacy",
        "terms": "Voorwaarden",
        "contact": "Contact",
        "impressum": "Colofon",
        "datenschutz": "Privacy",
    },
    "es": {
        "aviso_legal": "Aviso legal",
        "privacidad": "Privacidad",
        "privacy": "Privacidad",
        "terms": "Términos",
        "contact": "Contacto",
    },
    "pl": {
        "privacy": "Prywatność",
        "terms": "Regulamin",
        "contact": "Kontakt",
        "impressum": "Informacja prawna",
        "datenschutz": "Prywatność",
    },
    "ru": {
        "privacy": "Конфиденциальность",
        "terms": "Условия",
        "contact": "Контакты",
        "impressum": "Правовая информация",
        "datenschutz": "Конфиденциальность",
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
