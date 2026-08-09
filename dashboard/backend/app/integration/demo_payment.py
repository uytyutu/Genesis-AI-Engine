"""D0 — Demo Payment Bridge (internal demos only).

Rule: Demo Mode never ships as Production payment.
- Only tagged demo orders
- Never for ordinary customers
- Explicit UI: «Demo Payment — деньги не списываются»
- payment_mode = demo (not real paid money)
- Must not inflate real finance metrics
"""

from __future__ import annotations

import os
import re
from typing import Any

# Canonical Demo Company names (normalized)
_DEMO_COMPANY_ALIASES = frozenset(
    {
        "nordlicht möbel gmbh",
        "nordlicht moebel gmbh",
        "nordlicht möbel",
        "nordlicht moebel",
        "nordlicht furniture",
    }
)

DEMO_BANNER_RU = (
    "Demo Payment — средства не списываются. Только для внутренних тестов и demo-заказов."
)
DEMO_BANNER_DE = (
    "Demo Payment — es wird kein Geld abgebucht. Nur für interne Tests und Demo-Bestellungen."
)
DEMO_BANNER_EN = (
    "Demo Payment — no money is charged. Internal tests and demo orders only."
)


def _norm_name(name: str) -> str:
    s = (name or "").strip().lower()
    s = s.replace("ö", "o").replace("ä", "a").replace("ü", "u").replace("ß", "ss")
    s = re.sub(r"\s+", " ", s)
    return s


def is_production_locked() -> bool:
    """Hard production lock — demo bridge off unless explicitly allowed."""
    prod = os.getenv("GENESIS_PRODUCTION", "").strip() == "1"
    allow = os.getenv("GENESIS_ALLOW_DEMO_PAYMENT", "").strip() == "1"
    return prod and not allow


def demo_payment_bridge_enabled() -> bool:
    """Owner/demo environment gate — never open by default in production."""
    if is_production_locked():
        return False
    if os.getenv("GENESIS_ALLOW_DEMO_PAYMENT", "").strip() == "1":
        return True
    if os.getenv("GENESIS_DEMO_MODE", "").strip() == "1":
        return True
    if os.getenv("GENESIS_DEMO_PAYMENT", "").strip() == "1":
        return True
    # Local/dev default: bridge available for tagged demo orders only
    env = (os.getenv("GENESIS_ENV") or os.getenv("NODE_ENV") or "dev").strip().lower()
    if env in {"production", "prod"}:
        return False
    return True


def matches_demo_company_name(business_name: str) -> bool:
    n = _norm_name(business_name)
    if n in _DEMO_COMPANY_ALIASES:
        return True
    if n.startswith("nordlicht") and ("moebel" in n or "mobel" in n or "furniture" in n):
        return True
    # Golden Website / Golden Store Test companies (internal QA only)
    if n.startswith("golden test") or n.startswith("golden website") or n.startswith("golden store"):
        return True
    return False


def matches_demo_email(email: str) -> bool:
    em = (email or "").strip().lower()
    if not em or "@" not in em:
        return False
    local, _, domain = em.partition("@")
    if local.startswith("golden.") or local.startswith("golden+"):
        return True
    if domain in {"example.com", "example.org", "test.local", "localhost"}:
        return True
    return False


def should_tag_demo_order(payload: dict[str, Any]) -> bool:
    """True when create payload is an intentional demo order."""
    if not demo_payment_bridge_enabled():
        return False
    if payload.get("demo") is True or str(payload.get("demo") or "").lower() in {
        "1",
        "true",
        "yes",
    }:
        return True
    if str(payload.get("payment_mode") or "").lower() == "demo":
        return True
    if matches_demo_company_name(str(payload.get("business_name") or "")):
        return True
    return matches_demo_email(str(payload.get("email") or ""))


def is_demo_order(order: dict[str, Any] | None) -> bool:
    if not isinstance(order, dict):
        return False
    if str(order.get("payment_mode") or "").lower() == "demo":
        return True
    if order.get("demo") is True or order.get("is_demo") is True:
        return True
    if matches_demo_company_name(str(order.get("business_name") or "")):
        return True
    return matches_demo_email(str(order.get("email") or ""))


def assert_demo_payment_allowed(order: dict[str, Any]) -> None:
    if not demo_payment_bridge_enabled():
        raise ValueError("demo_payment_disabled")
    if not is_demo_order(order):
        raise ValueError("not_a_demo_order")


def demo_banner(ui_lang: str | None = None) -> str:
    lang = (ui_lang or "de")[:2].lower()
    if lang == "ru":
        return DEMO_BANNER_RU
    if lang == "en":
        return DEMO_BANNER_EN
    return DEMO_BANNER_DE


def demo_public_flags(order: dict[str, Any], *, ui_lang: str | None = None) -> dict[str, Any]:
    demo = is_demo_order(order)
    bridge = demo_payment_bridge_enabled()
    available = (
        demo
        and bridge
        and str(order.get("status") or "")
        in {
            "pending_confirmation",
            "confirmed",
            "awaiting_payment",
            "draft",
        }
        and not order.get("paid_at")
    )
    return {
        "demo": demo,
        "payment_mode": "demo"
        if demo or str(order.get("payment_mode") or "") == "demo"
        else (order.get("payment_mode") or None),
        "demo_payment_available": available,
        "demo_payment_banner": demo_banner(ui_lang) if demo else None,
        "demo_note": (
            "Demo Payment — internal / Golden Test only. Never for ordinary customers."
            if demo
            else None
        ),
    }
