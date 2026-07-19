"""Research-only Animated Landing price proposals per market.

NOT wired into Path A checkout / Stripe / packages. CEO decision after Claude quality report.
Formula: classic checkout anchors × animated uplift (Business/Premium heavier).
"""

from __future__ import annotations

from typing import Any

from app.factory.market_delivery import PATH_A_DELIVERY_MARKETS
from app.integration.commerce_engine import PACKAGE_IDS, resolve_final_offer
from app.integration.market_registry import format_amount, get_market

# Uplift vs classic Path A tiers — research proposal only.
_ANIMATED_UPLIFT: dict[str, float] = {
    "basic": 1.50,
    "business": 1.55,
    "premium": 1.65,
}


def _round_money(amount: float, currency: str) -> int:
    code = (currency or "EUR").upper()
    if code in ("PLN", "UAH", "CZK", "JPY", "KRW", "HUF"):
        return int(round(amount / 10.0) * 10)
    if amount >= 1000:
        return int(round(amount / 10.0) * 10)
    return int(round(amount))


def animated_offer_for_market(market_code: str, package_id: str) -> dict[str, Any]:
    classic = resolve_final_offer(package_id, market_code)
    uplift = _ANIMATED_UPLIFT.get(package_id, 1.5)
    amount = _round_money(float(classic.amount) * uplift, classic.currency)
    return {
        "market_code": classic.market_code,
        "package_id": f"animated_{package_id}",
        "classic_package_id": package_id,
        "amount": amount,
        "currency": classic.currency,
        "symbol": classic.symbol,
        "price_label": format_amount(amount, classic.symbol),
        "uplift": uplift,
        "classic_amount": classic.amount,
        "classic_price_label": classic.price_label,
        "status": "research_proposal",
        "checkout_wired": False,
    }


def list_animated_research_prices() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for code in PATH_A_DELIVERY_MARKETS:
        market = get_market(code)
        # Skip registry fallbacks that are not the requested market.
        if str(market.code).upper() != str(code).upper():
            continue
        entry: dict[str, Any] = {
            "market_code": market.code,
            "currency": market.currency,
            "symbol": market.symbol,
            "packages": {},
        }
        for tier in PACKAGE_IDS:
            offer = animated_offer_for_market(market.code, tier)
            entry["packages"][tier] = {
                "animated_amount": offer["amount"],
                "animated_label": offer["price_label"],
                "classic_amount": offer["classic_amount"],
                "classic_label": offer["classic_price_label"],
                "uplift": offer["uplift"],
            }
        rows.append(entry)
    return rows
