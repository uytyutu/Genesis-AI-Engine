"""Ownership boundaries for Virtus AI edits / intents."""

from __future__ import annotations

from typing import Any, Iterable

from app.factory.commerce_gates import ai_may_edit, normalize_owned_types, upsell_for


def check_ownership(
    message: str,
    *,
    products: Iterable[Any] | None = None,
    commerce_mode: str | None = None,
    package_id: str | None = None,
) -> dict[str, Any]:
    """Return {allowed, upsell?} for a free-text intent."""
    owned = normalize_owned_types(products)
    text = (message or "").strip()

    # Product-upsell intents
    upsell_needles = (
        "crm",
        "чат-бот",
        "чатбот",
        "chatbot",
        "автоматизац",
        "email-маркетинг",
        "whatsapp автоматиз",
        "онлайн-запис",
        "онлайн запис",
        "бронир",
        "booking",
        "интернет-магазин",
        "подключи магазин",
        "добавь crm",
        "добавь бота",
    )
    low = text.lower()
    if any(n in low for n in upsell_needles):
        # Store add is ok if they already own store and ask to add products
        if "товар" in low and "store" in owned:
            return {"allowed": True, "owned": sorted(owned)}
        if not ai_may_edit(low, owned=owned, commerce_mode=commerce_mode, package_id=package_id):
            u = upsell_for(text)
            return {"allowed": False, "owned": sorted(owned), "upsell": u}

    if ai_may_edit(low, owned=owned, commerce_mode=commerce_mode, package_id=package_id):
        return {"allowed": True, "owned": sorted(owned)}

    # Default: site edits need website
    if "website" not in owned and "store" not in owned:
        u = upsell_for("website")
        u["message"] = (
            "Сначала нужен сайт или магазин в Workspace. "
            "После покупки Virtus AI сможет менять страницы, медиа и тексты."
        )
        u["product"] = "website"
        u["label"] = "Website"
        u["cta"] = {"label": "Заказать сайт", "href": "/order?form=1"}
        return {"allowed": False, "owned": sorted(owned), "upsell": u}

    return {"allowed": True, "owned": sorted(owned)}
