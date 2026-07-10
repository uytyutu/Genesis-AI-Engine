"""Global Market Database — public API.

Stage 1: 29 markets in market_registry_v1.py
Stage 2: regional fallbacks for unlisted countries

Extend markets in market_registry_v1 only — logic reads registry here.
"""

from __future__ import annotations

from app.integration.market_registry_schema import (
    ALL_MARKET_SERVICES,
    ALL_WEBSITE_PROJECT_TYPES,
    PROJECT_BUSINESS_WEBSITE,
    PROJECT_TYPE_LABELS,
    MarketPriceRange,
    MarketProfile,
    ServicePricing,
    WebsiteProjectPricing,
    project_type_label,
)
from app.integration.market_registry_v1 import (
    MARKET_AE,
    MARKET_AT,
    MARKET_AU,
    MARKET_BE,
    MARKET_BR,
    MARKET_CA,
    MARKET_CH,
    MARKET_CZ,
    MARKET_DE,
    MARKET_DEFAULT,
    MARKET_ES,
    MARKET_FR,
    MARKET_GB,
    MARKET_HU,
    MARKET_IN,
    MARKET_IT,
    MARKET_JP,
    MARKET_KR,
    MARKET_MX,
    MARKET_NL,
    MARKET_NZ,
    MARKET_PL,
    MARKET_RO,
    MARKET_SA,
    MARKET_SG,
    MARKET_SK,
    MARKET_UA,
    MARKET_US,
    MARKET_ZA,
    MARKET_REGISTRY,
    STAGE1_MARKET_CODES,
)

# Backward compat alias
ServicePriceBand = MarketPriceRange


def get_market(market_code: str | None) -> MarketProfile:
    code = (market_code or MARKET_DEFAULT).upper()
    return MARKET_REGISTRY.get(code) or MARKET_REGISTRY[MARKET_DEFAULT]


def list_active_markets(*, exclude_default: bool = True) -> list[MarketProfile]:
    rows = list(MARKET_REGISTRY.values())
    if exclude_default:
        rows = [m for m in rows if m.code != MARKET_DEFAULT]
    return sorted(rows, key=lambda m: m.name("en"))


def format_amount(amount: int, symbol: str) -> str:
    return f"{amount:,}".replace(",", " ") + f" {symbol}"


def format_orientational_range(
    market_code: str,
    service_id: str = "website",
    *,
    project_type: str = PROJECT_BUSINESS_WEBSITE,
    locale: str = "ru",
) -> str:
    market = get_market(market_code)
    if service_id == "website":
        band = market.project_range(project_type)
    else:
        band = market.service_range(service_id)
    if not band:
        return ""
    lo = format_amount(band.from_amount, market.symbol)
    hi = format_amount(band.to_amount, market.symbol)
    label = project_type_label(project_type, locale=locale) if service_id == "website" else service_id
    return f"{market.name(locale)} · {label}: ориентировочно {lo} – {hi}"


def registry_summary_for_vector() -> str:
    lines: list[str] = []
    for m in list_active_markets():
        b = m.website_projects.business_website
        intel = m.intelligence
        lines.append(
            f"- **{m.name('ru')}** ({m.code}): Business Website {b.from_amount}–{b.to_amount} {m.symbol} "
            f"· avg {b.average_market} · {m.currency} · competition {intel.competition_level} "
            f"· factor {intel.market_factor} · review {intel.last_review}"
        )
    return "\n".join(lines)
