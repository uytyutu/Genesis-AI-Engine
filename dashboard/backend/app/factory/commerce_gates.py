"""Runtime commerce gates — Standalone vs Connected Workspace surfaces.

Canon: docs/canon/VIRTUS_AI_WORKSPACE.md
Pricing lives in commerce_model.py; this module decides what the client may see / edit.
"""

from __future__ import annotations

from typing import Any, Iterable, Literal

from app.factory.commerce_model import CommerceMode, is_connected, normalize_commerce_mode

SurfaceId = str
CommerceModeName = Literal["standalone", "connected"]

# Nav / AI surface keys (FE + Virtus AI share these ids)
STANDALONE_SURFACES: tuple[str, ...] = (
    "dashboard",
    "site",
    "pages",
    "media",
    "texts",
    "contacts",
    "products",  # store catalog
    "orders",  # store orders
    "settings",
    "backup",
    "domain",
    "stats_basic",
    "marketplace",
    "support",
    "billing",
)

CONNECTED_EXTRA_SURFACES: tuple[str, ...] = (
    "ai_assistant",
    "crm",
    "analytics",
    "chatbots",
    "automations",
    "email_marketing",
    "whatsapp",
    "booking",
    "notifications",
    "campaign_studio",
)

# Intent keywords → product / surface that must be owned
INTENT_PRODUCT: dict[str, str] = {
    "crm": "crm",
    "чат-бот": "chatbot",
    "чатбот": "chatbot",
    "chatbot": "chatbot",
    "бот": "chatbot",
    "автоматизац": "automation",
    "automation": "automation",
    "email-маркетинг": "email_marketing",
    "email marketing": "email_marketing",
    "whatsapp автоматиз": "whatsapp",
    "онлайн-запис": "booking",
    "онлайн запис": "booking",
    "booking": "booking",
    "бронир": "booking",
    "интернет-магазин": "store",
    "магазин": "store",
    "online store": "store",
    "campaign": "campaign_studio",
}


def normalize_owned_types(products: Iterable[Any] | None) -> set[str]:
    """Map portal/order product rows to coarse ownership keys."""
    owned: set[str] = set()
    for p in products or []:
        if isinstance(p, dict):
            t = str(p.get("product_type") or p.get("type") or "").lower()
            pid = str(p.get("product_id") or p.get("id") or "").lower()
        else:
            t = str(getattr(p, "product_type", "") or getattr(p, "type", "") or "").lower()
            pid = str(getattr(p, "product_id", "") or getattr(p, "id", "") or "").lower()
        blob = f"{t} {pid}"
        if "website" in blob or "site" in blob or "landing" in blob:
            owned.add("website")
        if "store" in blob or "shop" in blob or "ecommerce" in blob:
            owned.add("store")
        if "chatbot" in blob or "bot" in blob or "vector" in blob:
            owned.add("chatbot")
        if "crm" in blob:
            owned.add("crm")
        if "booking" in blob or "calendar" in blob:
            owned.add("booking")
        if "automat" in blob:
            owned.add("automation")
        if "email" in blob and "marketing" in blob:
            owned.add("email_marketing")
        if "whatsapp" in blob:
            owned.add("whatsapp")
        if "analytics" in blob:
            owned.add("analytics")
        if "campaign" in blob or "marketing_studio" in blob:
            owned.add("campaign_studio")
    return owned


def owned_surfaces(
    products: Iterable[Any] | None = None,
    *,
    commerce_mode: str | None = None,
    package_id: str | None = None,
) -> list[str]:
    """Allowlisted Workspace surface ids for this client."""
    mode = normalize_commerce_mode(package_id, commerce_mode=commerce_mode).commerce_mode
    owned = normalize_owned_types(products)
    surfaces = list(STANDALONE_SURFACES)

    # Hide store-only nav when no store
    if "store" not in owned:
        surfaces = [s for s in surfaces if s not in ("products", "orders")]

    if mode == "connected" or "chatbot" in owned:
        for s in CONNECTED_EXTRA_SURFACES:
            if s not in surfaces:
                surfaces.append(s)
        # Campaign studio always coming — still listed for Connected
    else:
        # Standalone may still open marketplace + support
        pass

    return surfaces


def surface_requires_connected(surface: str) -> bool:
    return (surface or "").strip().lower() in CONNECTED_EXTRA_SURFACES


def ai_may_edit(
    surface_or_intent: str,
    *,
    owned: Iterable[str] | None = None,
    commerce_mode: str | None = None,
    package_id: str | None = None,
) -> bool:
    """True if Virtus AI may change this surface under ownership rules."""
    key = (surface_or_intent or "").strip().lower()
    owned_set = {str(x).lower() for x in (owned or [])}
    mode = normalize_commerce_mode(package_id, commerce_mode=commerce_mode)

    # Core site surfaces — need website
    site_keys = {
        "site",
        "pages",
        "media",
        "texts",
        "contacts",
        "settings",
        "domain",
        "backup",
        "stats_basic",
        "website",
        "hero",
        "seo",
    }
    if key in site_keys or any(k in key for k in ("страниц", "фото", "контакт", "hero", "услуг")):
        return "website" in owned_set or "store" in owned_set

    if key in ("products", "orders", "store") or "товар" in key or "цен" in key:
        return "store" in owned_set

    if key in ("chatbots", "chatbot", "ai_assistant") or "бот" in key:
        return "chatbot" in owned_set or mode.ecosystem

    if key in ("crm",) or key.startswith("crm"):
        return "crm" in owned_set or mode.ecosystem

    if key in ("automations", "automation"):
        return "automation" in owned_set or mode.ecosystem

    if key in ("booking",):
        return "booking" in owned_set or mode.ecosystem

    if key in ("email_marketing", "whatsapp", "analytics", "notifications", "campaign_studio"):
        return key.replace("_marketing", "") in owned_set or key in owned_set or mode.ecosystem

    # Dashboard / marketplace always ok to discuss
    if key in ("dashboard", "marketplace", "support", "billing"):
        return True

    return False


def upsell_for(intent: str) -> dict[str, Any]:
    """Honest upsell payload when intent targets an unowned product."""
    text = (intent or "").strip().lower()
    product = "connected"
    label = "Virtus Core Connected"
    price = "499 € + 99 €/мес"
    href = "/client/shop"
    blurb = (
        "Эта возможность относится к отдельному продукту или к Connected. "
        "После подключения модуль интегрируется в ваш текущий проект — "
        "без переноса данных и без нового сайта."
    )

    for needle, prod in INTENT_PRODUCT.items():
        if needle in text:
            product = prod
            break

    catalog = {
        "crm": ("CRM", "149 €", "Заявки, клиенты и история в одном месте."),
        "chatbot": ("AI Chatbot", "99 €", "Диалоги с клиентами на сайте и в мессенджерах."),
        "booking": (
            "Booking System",
            "79 €",
            "Календарь, формы записи и управление бронированиями на вашем сайте.",
        ),
        "email_marketing": ("Email Automation", "69 €", "Письма и последовательности для клиентов."),
        "whatsapp": ("WhatsApp Automation", "59 €", "Уведомления и диалоги в WhatsApp."),
        "store": ("Online Store", "299 €", "Каталог, корзина и заказы в вашем Workspace."),
        "automation": ("Automation", "от 69 €", "Сценарии между сайтом, заявками и уведомлениями."),
        "campaign_studio": ("Marketing Studio", "Coming Soon", "Кампании и креативы — скоро."),
        "connected": (
            "Virtus Core Connected",
            "499 € + 99 €/мес",
            "Экосистема: CRM, AI, автоматизации, аналитика в том же Workspace.",
        ),
    }
    if product in catalog:
        label, price, detail = catalog[product]
        blurb = f"{detail} {blurb}"

    return {
        "ok": False,
        "reason": "not_owned",
        "product": product,
        "label": label,
        "price_hint": price,
        "message": blurb,
        "cta": {"label": f"Подключить {label}", "href": href},
        "canon": "VIRTUS_AI_WORKSPACE",
    }


def workspace_nav_spec(
    *,
    commerce_mode: str | None = None,
    package_id: str | None = None,
    products: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """JSON for FE ClientWorkspaceShell."""
    res = normalize_commerce_mode(package_id, commerce_mode=commerce_mode)
    owned = sorted(normalize_owned_types(products))
    surfaces = owned_surfaces(products, commerce_mode=res.commerce_mode)
    return {
        "commerce_mode": res.commerce_mode,
        "ecosystem": res.ecosystem,
        "label": res.label,
        "owned_products": owned,
        "surfaces": surfaces,
        "connected_extras": list(CONNECTED_EXTRA_SURFACES),
        "standalone_core": list(STANDALONE_SURFACES),
    }


__all__ = [
    "CONNECTED_EXTRA_SURFACES",
    "STANDALONE_SURFACES",
    "ai_may_edit",
    "normalize_owned_types",
    "owned_surfaces",
    "surface_requires_connected",
    "upsell_for",
    "workspace_nav_spec",
]
