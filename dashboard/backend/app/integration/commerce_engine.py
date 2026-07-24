"""Commerce Engine — localized checkout offers.

Path A amounts live in ``pricing_engine`` (SSOT). This module keeps market
resolution + thin wrappers so callers of ``resolve_final_offer`` keep working.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.market_context import resolve_market_context
from app.integration.market_registry import MARKET_DE, MARKET_PL, get_market
from app.integration.pricing_engine import (
    FinalOffer,
    WEBSITE_PACKAGE_IDS,
    list_path_a_packages,
    resolve_path_a_offer,
)

PACKAGE_IDS = WEBSITE_PACKAGE_IDS

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
    """Localized Path A price (website + repair) — delegates to pricing_engine."""
    return resolve_path_a_offer(package_id, market_code)


def resolve_checkout_packages(
    market_code: str,
    *,
    deliverables_by_id: dict[str, list[str]] | None = None,
    names_by_id: dict[str, str] | None = None,
) -> dict[str, Any]:
    """All website checkout tiers for a target market."""
    payload = list_path_a_packages(
        market_code,
        package_ids=WEBSITE_PACKAGE_IDS,
        deliverables_by_id=deliverables_by_id,
        names_by_id=names_by_id,
    )
    payload["delivery_support"] = _delivery_support_row(payload["market_code"])
    return payload


def _delivery_support_row(market_code: str) -> dict[str, Any]:
    from app.factory.market_delivery import market_delivery_support

    return market_delivery_support(market_code)


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
