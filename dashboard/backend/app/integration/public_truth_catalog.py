"""Mission 1 public catalog — single source when pricing_display.json is absent.

Prices match SalesOrderService.packages() (basic 350 / business 650 / premium 1200 €).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME
from app.integration.sales_order_service import _PACKAGES as SALES_PACKAGES

TRUTH_VERSION = "mission1-truth-1"
MISSION1_LANDING_TIMELINE = "5–14 дней"
MISSION1_PACKAGE_PRICES_EUR = (350, 650, 1200)


def _landing_packages() -> list[dict]:
    return list(SALES_PACKAGES.values())


def min_landing_price_eur(packages: list[dict[str, Any]] | None = None) -> int:
    pkgs = packages if packages is not None else _landing_packages()
    return min((p["price_eur"] for p in pkgs), default=350)


def format_order_packages_block(packages: list[dict[str, Any]] | None = None) -> str:
    pkgs = packages if packages is not None else _landing_packages()
    lines: list[str] = []
    for p in pkgs:
        deliverables = p.get("deliverables") or []
        d = "; ".join(deliverables[:4]) if deliverables else ""
        lines.append(f"- {p['name']} ({p['id']}): {p['price_eur']} € — {d}")
    return "\n".join(lines) if lines else "- Landing Basic (basic): 350 €"


def load_public_pricing_display(memory_dir: Path | None = None) -> dict[str, Any]:
    """Shared loader for API, frontend fallback, and Genesis Brain knowledge."""
    from app.integration.pricing_display_service import PricingDisplayService

    return PricingDisplayService(memory_dir=memory_dir).get_display()


def studio_unavailable_message() -> str:
    return (
        f"**{STUDIO_NAME}** (рабочая среда и подписка) **пока в разработке** — купить онлайн нельзя.\n\n"
        f"**Сейчас доступно:**\n"
        f"• Бесплатный разговор с {ASSISTANT_NAME} на **/site**\n"
        f"• Заказ **лендинга** под ключ — пакеты **350 / 650 / 1200 €** на **/order**"
    )


def unavailable_online_message(product_label: str) -> str:
    return (
        f"**{product_label}** под ключ **пока нельзя оформить на сайте**.\n\n"
        "Сейчас онлайн можно заказать **лендинг** — пакеты **350 / 650 / 1200 €** на **/order**.\n"
        "Расскажите, для какого бизнеса нужен сайт — подберём пакет после короткого разговора."
    )


def build_mission1_vector_commerce_rules(packages: list[dict[str, Any]] | None = None) -> str:
    """Mission 1 commerce block — injected into Vector system prompt and knowledge."""
    pkgs = packages if packages is not None else _landing_packages()
    packages_block = format_order_packages_block(pkgs)
    min_p = min_landing_price_eur(pkgs)
    platform = load_public_pricing_display().get("platform_status") or {}
    studio_note = platform.get("body") or studio_unavailable_message()

    return f"""## Mission 1 — что можно продавать публично (единая правда)

**Сейчас онлайн доступно только:**
- Разговор с {ASSISTANT_NAME} на `/site` (бесплатно)
- Заказ **лендинга** под ключ на `/order`

**Пакеты (только эти цены — никаких других):**
{packages_block}

**Срок:** ориентир **{MISSION1_LANDING_TIMELINE}** после подтверждения заказа; точный срок — на странице статуса.

**{STUDIO_NAME}:** {studio_note}
Не называй платные тарифы подписки. Workspace и подписки **не продаются**.

**Пока нельзя оформить онлайн:** интернет-магазин, Telegram/WhatsApp-бот, мобильное приложение, AI на сайте как отдельный продукт.
Скажи честно и предложи лендинг или разговор.

**Оплата:** только после согласия на заказ; Stripe — если подключён (иначе счёт вручную).

**Digital Consultant — пример (салон/кафе):**
Рекомендуй структуру сайта, затем ориентир **650 €** (Business) или **{min_p} €** (Basic) — только из пакетов выше.

Заказ — только после явного «да» / «оформляем» (GENESIS_ACTION → `/order?package=…`)."""


def build_truth_pricing_display() -> dict:
    packages = _landing_packages()
    min_price = min((p["price_eur"] for p in packages), default=350)

    return {
        "version": TRUTH_VERSION,
        "disclaimer": {
            "ru": (
                f"Сейчас онлайн можно заказать лендинг ({min_price}–1200 €). "
                f"{STUDIO_NAME} и другие услуги — по мере запуска; цены в чате и на /order совпадают."
            ),
        },
        "platform_status": {
            "label": "Virtus Studio — в разработке",
            "body": (
                f"Подписка {STUDIO_NAME} пока недоступна для покупки. "
                f"Сейчас: бесплатный разговор с Vector на /site и заказ лендинга на /order."
            ),
        },
        "capabilities": None,
        "service_vs_product": None,
        "anti_cannibalization": None,
        "comparison": None,
        "service_categories": [
            {
                "id": "landing",
                "name": "Лендинг под ключ",
                "description": (
                    f"Обсудите задачу с Vector на /site — затем оформите заказ. "
                    f"Пакеты Basic / Business / Premium совпадают с формой на /order."
                ),
                "items": [
                    {
                        "id": "landing",
                        "name": "Landing Page",
                        "price_label": f"от {min_price} €",
                        "timeline": "5–14 дней",
                        "includes": packages[0]["deliverables"][:4]
                        if packages
                        else ["1 страница", "Адаптив", "Контакты", "SEO-база"],
                        "description": "Одностраничный сайт — цена и состав пакета на шаге заказа",
                        "cta": "Заказать",
                        "cta_href": "/order",
                        "available": True,
                    },
                ],
            },
        ],
        "subscriptions": [
            {
                "id": "free",
                "name": "Free",
                "price_eur_month": 0,
                "price_label": "0 €",
                "period": "/мес",
                "audience": "Познакомиться с Vector",
                "tagline": "Чат на /site",
                "features": ["Разговор с Vector", "Обсуждение идеи", "Ориентир по цене лендинга"],
                "cta": "Начать на /site",
                "cta_href": "/site",
                "available": True,
            },
        ],
        "services": [],
        "business_units": [],
    }
