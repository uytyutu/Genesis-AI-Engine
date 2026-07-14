"""Commerce Engine — localized checkout offers from market registry.

Thin layer between market_registry and sales_order_service.
Dynamic pricing is one capability; checkout resolution is the Mission 1 surface.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.integration.market_context import resolve_market_context
from app.integration.market_registry import (
    MARKET_DE,
    MARKET_PL,
    checkout_price_scale,
    format_amount,
    get_market,
)

PACKAGE_IDS = ("basic", "business", "premium")

# Germany canonical checkout anchors (SalesOrderService legacy tiers).
_DE_CHECKOUT_ANCHORS: dict[str, int] = {
    "basic": 350,
    "business": 650,
    "premium": 1200,
}

_POLISH_CITY_MARKERS: tuple[str, ...] = (
    "kraków",
    "krakow",
    "warszawa",
    "warsaw",
    "wrocław",
    "wroclaw",
    "gdańsk",
    "gdansk",
    "poznań",
    "poznan",
    "łódź",
    "lodz",
    "katowice",
    "lublin",
    "краков",
    "варшав",
    "польш",
    "polska",
    "poland",
)


@dataclass(frozen=True)
class FinalOffer:
    package_id: str
    amount: int
    currency: str
    symbol: str
    market_code: str
    price_label: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "amount": self.amount,
            "currency": self.currency,
            "symbol": self.symbol,
            "market_code": self.market_code,
            "price_label": self.price_label,
        }


def resolve_checkout_market(
    *,
    market_code: str | None = None,
    city: str | None = None,
    visitor_id: str | None = None,
    memory_dir: Path | None = None,
    extra_text: str | None = None,
) -> str:
    """Target market for checkout — dialogue and business context, never IP."""
    if market_code and market_code.strip():
        return get_market(market_code.strip()).code

    chunks: list[str] = []
    if extra_text:
        chunks.append(extra_text.strip())
    if visitor_id and memory_dir:
        chunks.extend(_visitor_market_hints(visitor_id, memory_dir))
    if city:
        chunks.append(city.strip())

    combined = "\n".join(c for c in chunks if c)
    if combined.strip():
        ctx = resolve_market_context(text=combined)
        code = (ctx.target_market_code or MARKET_DE).upper()
        target_kinds = {
            "target_explicit_ru",
            "target_explicit_en",
            "deliverable_for",
            "business_in",
            "business_in_ru",
            "targeting",
        }
        has_target = any(s.kind in target_kinds for s in ctx.signals)
        if has_target and code != "DEFAULT":
            return get_market(code).code
        if ctx.confidence in ("high", "medium") and code != "DEFAULT":
            return get_market(code).code

    if city:
        low = city.strip().lower()
        if any(marker in low for marker in _POLISH_CITY_MARKERS):
            return MARKET_PL

    return MARKET_DE


def resolve_final_offer(package_id: str, market_code: str) -> FinalOffer:
    """Localized fixed checkout price for a sales package tier."""
    tier = package_id if package_id in _DE_CHECKOUT_ANCHORS else "basic"
    market = get_market(market_code)
    scale = checkout_price_scale(market.code)
    amount = max(1, round(_DE_CHECKOUT_ANCHORS[tier] * scale))
    label = format_amount(amount, market.symbol)
    return FinalOffer(
        package_id=tier,
        amount=amount,
        currency=market.currency,
        symbol=market.symbol,
        market_code=market.code,
        price_label=label,
    )


def resolve_checkout_packages(
    market_code: str,
    *,
    deliverables_by_id: dict[str, list[str]] | None = None,
    names_by_id: dict[str, str] | None = None,
) -> dict[str, Any]:
    """All checkout tiers for a target market."""
    market = get_market(market_code)
    packages: list[dict[str, Any]] = []
    for tier in PACKAGE_IDS:
        offer = resolve_final_offer(tier, market.code)
        packages.append(
            {
                "id": tier,
                "name": (names_by_id or {}).get(tier, _default_name(tier)),
                "price_eur": float(offer.amount),
                "currency": offer.currency,
                "symbol": offer.symbol,
                "market_code": offer.market_code,
                "price_label": offer.price_label,
                "deliverables": list((deliverables_by_id or {}).get(tier, [])),
            }
        )
    return {
        "packages": packages,
        "market_code": market.code,
        "currency": market.currency,
        "symbol": market.symbol,
    }


def _default_name(tier: str) -> str:
    return {
        "basic": "Landing Basic",
        "business": "Landing Business",
        "premium": "Landing Premium",
    }.get(tier, tier)


def _visitor_market_hints(visitor_id: str, memory_dir: Path) -> list[str]:
    hints: list[str] = []
    try:
        from app.integration.project_platform.service import ProjectPlatformService

        state = ProjectPlatformService(memory_dir).get_for_visitor(visitor_id.strip()[:64])
    except Exception:
        return hints
    if not state.get("has_project") or not state.get("project"):
        return hints
    project = state["project"]
    identity = project.get("identity") or {}
    for key in ("title", "description", "summary"):
        val = str(identity.get(key) or "").strip()
        if val:
            hints.append(val)
    for item in project.get("journey", {}).get("items", []):
        val = str(item.get("value") or "").strip()
        if val:
            hints.append(val)
    return hints
