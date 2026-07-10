"""Global Market Database v1 — schema (Stage 1 markets, extensible).

Prices are orientational ranges tied to market intelligence metadata.
Final amount = preliminary project estimate after concept approval + complexity.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# --- Project types (digital solutions, not generic "website") --------------------

PROJECT_LANDING_PAGE = "landing_page"
PROJECT_BUSINESS_WEBSITE = "business_website"
PROJECT_CORPORATE_WEBSITE = "corporate_website"
PROJECT_ONLINE_STORE = "online_store"
PROJECT_RESTAURANT_WEBSITE = "restaurant_website"
PROJECT_MEDICAL_WEBSITE = "medical_website"
PROJECT_REAL_ESTATE_WEBSITE = "real_estate_website"
PROJECT_HOTEL_WEBSITE = "hotel_website"
PROJECT_LAW_FIRM_WEBSITE = "law_firm_website"
PROJECT_PORTFOLIO_WEBSITE = "portfolio_website"

PROJECT_TYPE_LABELS: dict[str, dict[str, str]] = {
    PROJECT_LANDING_PAGE: {"ru": "Landing Page", "en": "Landing Page"},
    PROJECT_BUSINESS_WEBSITE: {"ru": "Business Website", "en": "Business Website"},
    PROJECT_CORPORATE_WEBSITE: {"ru": "Corporate Website", "en": "Corporate Website"},
    PROJECT_ONLINE_STORE: {"ru": "Online Store", "en": "Online Store"},
    PROJECT_RESTAURANT_WEBSITE: {"ru": "Restaurant Website", "en": "Restaurant Website"},
    PROJECT_MEDICAL_WEBSITE: {"ru": "Medical Website", "en": "Medical Website"},
    PROJECT_REAL_ESTATE_WEBSITE: {"ru": "Real Estate Website", "en": "Real Estate Website"},
    PROJECT_HOTEL_WEBSITE: {"ru": "Hotel Website", "en": "Hotel Website"},
    PROJECT_LAW_FIRM_WEBSITE: {"ru": "Law Firm Website", "en": "Law Firm Website"},
    PROJECT_PORTFOLIO_WEBSITE: {"ru": "Portfolio", "en": "Portfolio"},
}

ALL_WEBSITE_PROJECT_TYPES: tuple[str, ...] = tuple(PROJECT_TYPE_LABELS.keys())

# Other Virtus Core services (same market structure)
SERVICE_BUSINESS_PLAN = "business_plan"
SERVICE_PRESENTATION = "presentation"
SERVICE_AUTOMATION = "automation"
SERVICE_AI_EMPLOYEE = "ai_employee"
SERVICE_CRM = "crm"
SERVICE_CHATBOT = "chatbot"
SERVICE_MOBILE_APP = "mobile_app"
SERVICE_DESKTOP_APP = "desktop_app"
SERVICE_GAME = "game_development"
SERVICE_MARKETING = "marketing_strategy"
SERVICE_SEO = "seo"
SERVICE_BRANDING = "branding"

ALL_MARKET_SERVICES: tuple[str, ...] = (
    "website",
    SERVICE_BUSINESS_PLAN,
    SERVICE_PRESENTATION,
    SERVICE_AUTOMATION,
    SERVICE_AI_EMPLOYEE,
    SERVICE_CRM,
    SERVICE_CHATBOT,
    SERVICE_MOBILE_APP,
    SERVICE_DESKTOP_APP,
    SERVICE_GAME,
    SERVICE_MARKETING,
    SERVICE_SEO,
    SERVICE_BRANDING,
)


@dataclass(frozen=True)
class MarketPriceRange:
    """Recommended orientational band — not a single fixed price."""

    from_amount: int
    to_amount: int
    average_market: int

    @property
    def midpoint(self) -> int:
        return self.average_market


@dataclass(frozen=True)
class WebsiteProjectPricing:
    landing_page: MarketPriceRange
    business_website: MarketPriceRange
    corporate_website: MarketPriceRange
    online_store: MarketPriceRange
    restaurant_website: MarketPriceRange
    medical_website: MarketPriceRange
    real_estate_website: MarketPriceRange
    hotel_website: MarketPriceRange
    law_firm_website: MarketPriceRange
    portfolio_website: MarketPriceRange

    def get(self, project_type: str) -> MarketPriceRange | None:
        return getattr(self, project_type, None)


@dataclass(frozen=True)
class ServicePricing:
    standard: MarketPriceRange


@dataclass(frozen=True)
class MarketIntelligenceMeta:
    competition_level: str  # low | medium | high
    market_factor: float
    last_review: str
    confidence: str  # low | medium | high
    update_source: str = "Global Market Database v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "competition_level": self.competition_level,
            "market_factor": self.market_factor,
            "last_review": self.last_review,
            "confidence": self.confidence,
            "update_source": self.update_source,
        }


@dataclass(frozen=True)
class MarketProfile:
    code: str
    names: dict[str, str]
    currency: str
    symbol: str
    locale_default: str
    legal_requirements: tuple[str, ...]
    requires: tuple[str, ...]
    intelligence: MarketIntelligenceMeta
    website_projects: WebsiteProjectPricing
    services: dict[str, ServicePricing] = field(default_factory=dict)
    document_formats: tuple[str, ...] = ()
    region_fallback: str | None = None  # Stage 2: e.g. "Balkans"

    def name(self, locale: str = "ru") -> str:
        return self.names.get(locale) or self.names.get("en") or self.code

    def project_range(self, project_type: str) -> MarketPriceRange | None:
        return self.website_projects.get(project_type)

    def service_range(self, service_id: str) -> MarketPriceRange | None:
        row = self.services.get(service_id)
        return row.standard if row else None

    # Backward compat — business website as default "website" band
    @property
    def website(self) -> MarketPriceRange | None:
        return self.website_projects.business_website

    def service_band_legacy(self, service_id: str) -> MarketPriceRange | None:
        if service_id == "website":
            return self.website
        return self.service_range(service_id)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "names": self.names,
            "currency": self.currency,
            "symbol": self.symbol,
            "locale_default": self.locale_default,
            "legal_requirements": list(self.legal_requirements),
            "requires": list(self.requires),
            "intelligence": self.intelligence.to_dict(),
            "region_fallback": self.region_fallback,
        }


def project_type_label(project_type: str, *, locale: str = "ru") -> str:
    row = PROJECT_TYPE_LABELS.get(project_type) or {}
    return row.get(locale) or row.get("en") or project_type
