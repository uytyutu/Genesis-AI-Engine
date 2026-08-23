# -*- coding: utf-8 -*-
"""Vector coaching notifications — ephemeral teach/nudge cards (NOT a chat).

Vector appears, teaches one business action, then disappears.
Never a ChatGPT-style conversation surface for this mode.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4


def build_coaching_notifications(
    *,
    niche: str = "",
    business_name: str = "",
    has_website: bool = False,
    has_shop: bool = False,
    gift_unlimited: bool = False,
) -> list[dict[str, Any]]:
    """Return short-lived notification cards for Client Workspace."""
    name = business_name or "Ihr Business"
    niche_l = (niche or "").lower()
    cards: list[dict[str, Any]] = []

    def _card(title: str, body: str, action: str, href: str, ttl_sec: int = 12) -> dict[str, Any]:
        return {
            "id": f"vcn-{uuid4().hex[:10]}",
            "kind": "coaching_notification",
            "not_chat": True,
            "title": title,
            "body": body,
            "action_label": action,
            "href": href,
            "ttl_sec": ttl_sec,
            "auto_dismiss": True,
        }

    if has_website:
        cards.append(
            _card(
                "Vorschau prüfen",
                f"{name}: Öffnen Sie die Live-Vorschau und prüfen Sie Lesbarkeit auf dem Handy.",
                "Website öffnen",
                "/client/products",
            )
        )
    if has_shop:
        cards.append(
            _card(
                "Katalog pflegen",
                "Produkte, Preise und Kategorien können Sie direkt im Shop-Admin ändern — die Storefront aktualisiert sich nach dem Speichern.",
                "Shop verwalten",
                "/client/products",
            )
        )
    if niche_l in ("gift_boxes", "beauty_gifts") or "gift" in niche_l:
        cards.append(
            _card(
                "Markt-Hinweis · Gift Boxes",
                "Emotionale Käufe: starke Box-Fotos, klare Kategorien (Geburtstag, Self Care, Romantik) und ein klarer CTA «Box wählen» erhöhen Conversion.",
                "Kategorien prüfen",
                "/client/shop",
                ttl_sec=16,
            )
        )
        cards.append(
            _card(
                "Risiko & Chance",
                "Risiko: generische Beauty-Salon-Bilder zerstören Vertrauen. Chance: Packaging-Ritual (öffnen → Inhalt) als cinematic Story verkauft Premium-Preise.",
                "Verstanden",
                "/client",
                ttl_sec=18,
            )
        )
    if gift_unlimited:
        cards.append(
            _card(
                "Unlimited Workspace",
                "Dieser Account ist als Geschenk freigeschaltet: Website + Shop + Module ohne Paket-Limits. Gewöhnliche Kunden nutzen Marketplace Add-ons.",
                "Zum Workspace",
                "/client",
            )
        )
    else:
        cards.append(
            _card(
                "Marketplace",
                "Zusatzmodule (Booking, CRM, Marketing) erscheinen als Included / Available / Coming Soon — keine Rückkehr zur öffentlichen Vitrine nötig.",
                "Marketplace",
                "/client/shop",
            )
        )

    # Cap: Vector teaches, does not spam
    return cards[:4]


def coaching_payload_for_me(me: dict[str, Any], orders: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    orders = orders or []
    has_web = any(
        str(o.get("package_id") or "") in ("premium", "business", "basic", "connected", "standalone")
        and str(o.get("product_kind") or "website") != "shop"
        for o in orders
    ) or any("website" in str(o.get("product_kind") or "") for o in orders)
    has_shop = any(
        str(o.get("package_id") or "") == "ecommerce_shop"
        or str(o.get("product_kind") or "") == "shop"
        for o in orders
    )
    return {
        "mode": "notifications",
        "not_chat": True,
        "notifications": build_coaching_notifications(
            niche=str(me.get("niche") or me.get("primary_niche") or ""),
            business_name=str(me.get("company_display_name") or me.get("name") or ""),
            has_website=has_web or bool(me.get("gift_unlimited")),
            has_shop=has_shop or bool(me.get("gift_unlimited")),
            gift_unlimited=bool(me.get("gift_unlimited") or me.get("unlimited")),
        ),
    }
