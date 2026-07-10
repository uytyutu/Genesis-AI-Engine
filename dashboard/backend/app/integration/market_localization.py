"""Full market localization — currency, prices, legal context, document norms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.integration.market_context import ProjectMarketContext, resolve_market_context
from app.integration.market_registry import (
    MARKET_DEFAULT,
    PROJECT_BUSINESS_WEBSITE,
    format_orientational_range,
    get_market,
)
from app.integration.product_line import ASSISTANT_NAME, BRAND_NAME


@dataclass
class LocalizedCommerce:
    market_code: str
    market_name: str
    currency: str
    currency_symbol: str
    locale: str
    legal_requirements: tuple[str, ...]
    document_formats: tuple[str, ...]
    competition_level: str
    market_factor: float
    last_review: str
    orientational_website_range: str
    orientational_website_min: int
    orientational_website_max: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "market_code": self.market_code,
            "market_name": self.market_name,
            "currency": self.currency,
            "currency_symbol": self.currency_symbol,
            "locale": self.locale,
            "legal_requirements": list(self.legal_requirements),
            "competition_level": self.competition_level,
            "market_factor": self.market_factor,
            "last_review": self.last_review,
            "orientational_website_range": self.orientational_website_range,
        }


def resolve_localized_commerce(
    ctx: ProjectMarketContext | None = None,
    *,
    messages: list[dict[str, str]] | None = None,
    text: str | None = None,
    ui_locale: str | None = None,
    project_type: str = PROJECT_BUSINESS_WEBSITE,
) -> LocalizedCommerce:
    if ctx is None:
        ctx = resolve_market_context(messages=messages, text=text, ui_locale=ui_locale)
    code = ctx.target_market_code or MARKET_DEFAULT
    loc = ctx.project_language or ui_locale or "ru"
    if loc not in ("ru", "en", "de", "pl", "uk", "fr", "es", "ja"):
        loc = "en"
    market = get_market(code)
    band = market.project_range(project_type)
    intel = market.intelligence
    range_label = format_orientational_range(code, "website", project_type=project_type, locale=loc)
    return LocalizedCommerce(
        market_code=market.code,
        market_name=market.name(loc),
        currency=market.currency,
        currency_symbol=market.symbol,
        locale=market.locale_default if code != MARKET_DEFAULT else loc,
        legal_requirements=market.legal_requirements,
        document_formats=market.document_formats,
        competition_level=intel.competition_level,
        market_factor=intel.market_factor,
        last_review=intel.last_review,
        orientational_website_range=range_label,
        orientational_website_min=band.from_amount if band else 0,
        orientational_website_max=band.to_amount if band else 0,
    )


def full_localization_rules_for_vector() -> str:
    return f"""## Полная локализация {BRAND_NAME}

Адаптируй под **целевой рынок проекта** (не VPN, не IP):

1. **Язык** — один язык на весь проект.
2. **Валюта** — USD, ¥, £, zł, ₴, €… по рынку, не «евро всем».
3. **Предварительная смета проекта** — после согласования концепции, в валюте рынка.
4. **Юридические требования** — по таблице рынков (Impressum, RGPD, RODO…).
5. **Формат документов** — под нормы страны; при сомнении — честно сказать.

**Не показывать цену в начале диалога.** Сначала концепция и согласование.

Global Market Database v1 — 29 рынков; остальные → региональные модели (Stage 2).

{ASSISTANT_NAME} использует реестр; изменения цен — только через Market Intelligence + одобрение владельца."""
