"""Mission 1 public catalog — single source when pricing_display.json is absent.

Prices match SalesOrderService.packages() (basic 350 / business 650 / premium 1200 €).
"""

from __future__ import annotations

from app.integration.genesis_brain.public_brand import STUDIO_NAME
from app.integration.sales_order_service import _PACKAGES as SALES_PACKAGES

TRUTH_VERSION = "mission1-truth-1"


def _landing_packages() -> list[dict]:
    return list(SALES_PACKAGES.values())


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
