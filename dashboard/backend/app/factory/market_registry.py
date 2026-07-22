"""R3.4.2.1 — Market Registry (registration table for MarketProfile).

Adding a country = register a MarketProfile here (or via register()).
resolve() looks up the registry — not a growing if/else chain.
"""

from __future__ import annotations

from app.factory.market_delivery import normalize_market
from app.factory.market_profile import MarketProfile

ENGINE_ID = "market_registry_v1"
FALLBACK_MARKET = "DE"


class MarketRegistry:
    """Single registration table: market_code → MarketProfile."""

    def __init__(self, *, fallback_code: str = FALLBACK_MARKET) -> None:
        self._profiles: dict[str, MarketProfile] = {}
        self._fallback_code = (fallback_code or FALLBACK_MARKET).strip().upper() or FALLBACK_MARKET

    def register(self, profile: MarketProfile) -> None:
        code = (profile.market_code or "").strip().upper()
        if not code:
            raise ValueError("market_code_required")
        if profile.market_code != code:
            # Keep stored profile.market_code canonical uppercase
            from dataclasses import replace

            profile = replace(profile, market_code=code)
        self._profiles[code] = profile

    def get(self, market_code: str | None) -> MarketProfile | None:
        code = normalize_market(market_code)
        return self._profiles.get(code)

    def resolve(self, market_code: str | None) -> MarketProfile:
        code = normalize_market(market_code)
        if code in self._profiles:
            return self._profiles[code]
        fallback = self._profiles.get(self._fallback_code)
        if fallback is None:
            raise RuntimeError(f"market_registry_missing_fallback:{self._fallback_code}")
        return fallback

    def codes(self) -> tuple[str, ...]:
        return tuple(self._profiles.keys())

    def as_table(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for code in self.codes():
            p = self._profiles[code]
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


# Process-wide default registry — seeded by market_profile module.
DEFAULT_REGISTRY = MarketRegistry(fallback_code=FALLBACK_MARKET)


def get_registry() -> MarketRegistry:
    return DEFAULT_REGISTRY


def register_market(profile: MarketProfile, *, registry: MarketRegistry | None = None) -> None:
    (registry or DEFAULT_REGISTRY).register(profile)
