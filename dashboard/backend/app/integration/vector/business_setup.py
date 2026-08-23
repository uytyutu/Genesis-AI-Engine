"""Business Setup % + Launch/Growth checklist (Virtus AI Workspace canon)."""

from __future__ import annotations

from typing import Any

from app.integration.vector.capabilities import action_for, is_live


def _launch_checklist(
    *,
    has_website: bool,
    has_store: bool,
    product_count: int,
    email_connected: bool,
    analytics_live: bool,
    niche: str = "",
    commerce_mode: str = "standalone",
) -> dict[str, Any]:
    """Post-purchase Launch → Growth checklist."""
    n = (niche or "").lower()
    launch_items: list[dict[str, Any]] = [
        {
            "id": "site_created",
            "label": "Сайт создан",
            "done": has_website or has_store,
            "why": "База цифрового бизнеса — опубликованный проект в Workspace.",
            "href": "/client/site",
        },
        {
            "id": "domain",
            "label": "Домен",
            "done": False,
            "why": "Собственный домен повышает доверие сильнее бесплатных адресов.",
            "href": "/client/domain",
        },
        {
            "id": "hosting",
            "label": "Публикация / хостинг",
            "done": has_website or has_store,
            "why": "Сайт должен быть доступен клиентам 24/7.",
            "href": "/client/site",
        },
        {
            "id": "email",
            "label": "Корпоративная почта",
            "done": email_connected,
            "why": "Адрес info@вашдомен.de вызывает больше доверия, чем бесплатная почта.",
            "href": "/client/email" if commerce_mode == "connected" else "/client/contacts",
        },
        {
            "id": "whatsapp",
            "label": "WhatsApp",
            "done": False,
            "why": "Клиенты часто пишут в мессенджер быстрее, чем заполняют форму.",
            "href": "/client/whatsapp" if commerce_mode == "connected" else "/client/contacts",
        },
        {
            "id": "gbp",
            "label": "Google Business Profile",
            "done": False,
            "why": "Люди находят компанию в Maps и оставляют отзывы.",
            "href": "/client/contacts",
        },
        {
            "id": "social",
            "label": "Социальные сети",
            "done": False,
            "why": "Ссылки на Instagram / Facebook закрывают путь «проверить компанию».",
            "href": "/client/contacts",
        },
        {
            "id": "analytics",
            "label": "Аналитика",
            "done": analytics_live,
            "why": "Без цифр Virtus AI не сможет рекомендовать улучшения по фактам.",
            "href": "/client/analytics" if commerce_mode == "connected" else "/client/stats",
        },
        {
            "id": "seo",
            "label": "SEO",
            "done": False,
            "why": "Базовые title/description помогают поиску найти вас.",
            "href": "/client/texts",
        },
        {
            "id": "backup",
            "label": "Резервное копирование",
            "done": False,
            "why": "Бэкап защищает проект при сбоях хостинга.",
            "href": "/client/downloads",
        },
    ]
    if has_store:
        launch_items.insert(
            3,
            {
                "id": "first_products",
                "label": "Первые товары",
                "done": product_count >= 1,
                "why": "Магазин без товаров не продаёт — добавьте витрину.",
                "href": "/client/products",
            },
        )
    if any(x in n for x in ("restaurant", "food", "gastro")):
        launch_items.append(
            {
                "id": "menu",
                "label": "Меню",
                "done": False,
                "why": "Гости выбирают заведение по меню — добавьте блюда и цены.",
                "href": "/client/pages",
            }
        )
    if any(x in n for x in ("psych", "therapy", "dental", "clinic", "beauty")):
        launch_items.append(
            {
                "id": "booking",
                "label": "Онлайн-запись",
                "done": False,
                "why": "Календарь снижает трение записи. Модуль Booking — в Marketplace.",
                "href": "/client/booking" if commerce_mode == "connected" else "/client/shop",
                "upsell": commerce_mode != "connected",
            }
        )

    launch_done = all(i["done"] for i in launch_items[:3])
    all_launch_done = all(i["done"] for i in launch_items if not i.get("upsell"))

    growth: list[dict[str, Any]] = [
        {
            "id": "first_leads",
            "label": "Получить первые заявки",
            "done": False,
            "why": "Усильте Hero и WhatsApp, если форма почти не используется.",
            "href": "/client/site",
        },
        {
            "id": "reviews",
            "label": "Добавить отзывы",
            "done": False,
            "why": "Социальное доказательство повышает конверсию.",
            "href": "/client/pages",
        },
        {
            "id": "seo_grow",
            "label": "Улучшить SEO",
            "done": False,
            "why": "Страницы услуг часто недооценены поиском.",
            "href": "/client/texts",
        },
    ]
    if commerce_mode == "connected":
        growth.append(
            {
                "id": "crm_flow",
                "label": "Связать заявки с CRM",
                "done": False,
                "why": "Connected позволяет вести клиентов без таблиц.",
                "href": "/client/crm",
            }
        )

    stage = "growth" if all_launch_done else "launch"
    items = growth if stage == "growth" else launch_items
    next_step = next((i for i in items if not i["done"]), None)

    return {
        "stage": stage,
        "title": "Развитие бизнеса" if stage == "growth" else "Запуск бизнеса",
        "items": items,
        "next": next_step,
        "standalone_soft": commerce_mode != "connected",
        "note": (
            "Standalone: после запуска Virtus AI не навязывает CRM. "
            if commerce_mode != "connected"
            else "Connected: рекомендации экосистемы по фактам проекта."
        ),
        "soft_ready": launch_done,
    }


def build_business_setup(
    *,
    has_website: bool = False,
    has_store: bool = False,
    product_count: int = 0,
    branding_done: bool = False,
    store_published: bool = False,
    primary_store_order_id: str | None = None,
    payments_connected: bool = False,
    shipping_connected: bool = False,
    taxes_configured: bool = False,
    email_connected: bool = False,
    analytics_live: bool = False,
    marketing_live: bool = False,
    niche: str = "",
    commerce_mode: str = "standalone",
) -> dict[str, Any]:
    items: list[dict[str, Any]] = [
        {
            "id": "website",
            "label": "Website",
            "done": has_website,
            "weight": 12,
            "actionable": True,
            "action": action_for("open_products")
            if not has_website
            else {
                "id": "website_ok",
                "kind": "noop",
                "label": "Done",
                "status": "live",
            },
        },
        {
            "id": "store",
            "label": "Store",
            "done": has_store,
            "weight": 12,
            "actionable": True,
            "action": (
                action_for("open_store_admin", order_id=primary_store_order_id)
                if has_store and primary_store_order_id
                else action_for("open_products")
            ),
        },
        {
            "id": "products",
            "label": "Products",
            "done": product_count >= 1,
            "weight": 12,
            "actionable": is_live("store_products"),
            "meta": {"count": product_count},
            "action": action_for(
                "store_products",
                cta_override="Open Products",
            ),
        },
        {
            "id": "branding",
            "label": "Branding",
            "done": branding_done,
            "weight": 10,
            "actionable": is_live("store_design_logo"),
            "action": action_for("store_design_logo", cta_override="Open Design"),
        },
        {
            "id": "payments",
            "label": "Payments",
            "done": payments_connected,
            "weight": 12,
            "actionable": is_live("payments_stripe"),
            "action": action_for("payments_stripe"),
        },
        {
            "id": "shipping",
            "label": "Shipping",
            "done": shipping_connected,
            "weight": 10,
            "actionable": is_live("shipping_carriers"),
            "action": action_for("shipping_carriers", cta_override="Настроить"),
        },
        {
            "id": "taxes",
            "label": "Taxes",
            "done": taxes_configured,
            "weight": 8,
            "actionable": is_live("taxes_vat"),
            "action": action_for("taxes_vat"),
        },
        {
            "id": "email",
            "label": "Email",
            "done": email_connected,
            "weight": 8,
            "actionable": is_live("email_transactional"),
            "action": action_for("email_transactional"),
        },
        {
            "id": "analytics",
            "label": "Analytics",
            "done": analytics_live,
            "weight": 8,
            "actionable": False,
            "coming": "R3.4",
            "action": action_for("analytics"),
        },
        {
            "id": "marketing",
            "label": "Marketing",
            "done": marketing_live,
            "weight": 8,
            "actionable": False,
            "coming": "R3.4",
            "action": action_for("marketing"),
        },
    ]

    if store_published and has_store:
        for it in items:
            if it["id"] == "store":
                it["meta"] = {**(it.get("meta") or {}), "published": True}

    total_w = sum(int(i["weight"]) for i in items) or 1
    earned = sum(int(i["weight"]) for i in items if i["done"])
    pct = int(round(100 * earned / total_w))

    groups = {
        "Website": ["website"],
        "Store": ["store", "products"],
        "Brand": ["branding"],
        "Payments": ["payments", "shipping", "taxes", "email"],
        "Marketing": ["analytics", "marketing"],
    }
    bars: list[dict[str, Any]] = []
    for label, ids in groups.items():
        subset = [i for i in items if i["id"] in ids]
        tw = sum(int(i["weight"]) for i in subset) or 1
        ew = sum(int(i["weight"]) for i in subset if i["done"])
        bars.append(
            {
                "id": label.lower(),
                "label": label,
                "pct": int(round(100 * ew / tw)),
                "done": all(i["done"] for i in subset) if subset else False,
            }
        )

    next_item = next((i for i in items if not i["done"] and i.get("actionable")), None)
    if next_item is None:
        next_item = next((i for i in items if not i["done"]), None)

    launch = _launch_checklist(
        has_website=has_website,
        has_store=has_store,
        product_count=product_count,
        email_connected=email_connected,
        analytics_live=analytics_live,
        niche=niche,
        commerce_mode=commerce_mode or "standalone",
    )

    return {
        "ok": True,
        "title": "Запуск бизнеса" if launch["stage"] == "launch" else "Развитие бизнеса",
        "pct": pct,
        "bars": bars,
        "items": items,
        "next": next_item,
        "launch": launch,
        "note": "Virtus AI never fakes Connect for Coming modules. Ownership gates apply.",
    }
