"""Mission 1 public catalog — single source when pricing_display.json is absent.

Prices match SalesOrderService.packages() (basic 350 / business 650 / premium 1200 €).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME
from app.legal.vector_rules import legal_trust_rules_for_vector
from app.integration.project_platform.vector_rules import project_platform_rules_for_vector
from app.integration.delivery_engine.gate import delivery_rules_for_truth
from app.integration.market_intelligence import market_intelligence_rules_for_vector
from app.integration.market_localization import full_localization_rules_for_vector
from app.integration.platform_directive import platform_directive_v2_rules
from app.integration.global_pricing import global_pricing_rules_for_vector
from app.integration.market_context import market_detection_rules_for_vector
from app.integration.product_line import (
    ONE_TIME_SERVICES,
    SERVICE_WEBSITE,
    SUBSCRIPTION_TIERS,
    WEBSITE_PACKAGE_LABELS,
    universal_service_model_rules,
)
from app.integration.sales_order_service import _PACKAGES as SALES_PACKAGES

TRUTH_VERSION = "g23-commercial-1"
MISSION1_LANDING_TIMELINE = "oft ca. 15 Minuten"
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
        f"• Бесплатная работа с {ASSISTANT_NAME} в вашей цифровой компании\n"
        f"• Заказ **лендинга** под ключ — пакеты **350 / 650 / 1200 €** на странице заказа"
    )


def unavailable_online_message(product_label: str) -> str:
    return (
        f"**{product_label}** под ключ **пока нельзя оформить на сайте**.\n\n"
        "Сейчас онлайн можно заказать **лендинг** — пакеты **350 / 650 / 1200 €** на **/order**.\n"
        "Опишите задачу — подберём пакет под проект."
    )


def _build_service_categories(
    packages: list[dict[str, Any]],
    *,
    market_code: str = "DE",
) -> list[dict[str, Any]]:
    """Path A packages + pilot quote catalog + legacy one-time horizon rows."""
    from app.integration.pilot_service_catalog import public_pilot_categories

    categories: list[dict[str, Any]] = list(public_pilot_categories())
    order_href = f"/order?market={market_code}"

    # Keep priced Path A packages as explicit checkout cards (localized currency).
    website_items = [
        {
            "id": p["id"],
            "name": WEBSITE_PACKAGE_LABELS.get(p["id"], p["name"]),
            "price_label": p.get("price_label")
            or f"{p.get('price_eur')} {p.get('symbol') or '€'}",
            "timeline": MISSION1_LANDING_TIMELINE,
            "includes": p.get("deliverables", [])[:4],
            "description": "Einmalige Leistung — kein Abo",
            "cta": "Jetzt bestellen",
            "cta_href": order_href,
            "available": True,
            "tier": "checkout",
            "currency": p.get("currency"),
            "market_code": p.get("market_code") or market_code,
        }
        for p in packages
    ]
    categories.insert(
        0,
        {
            "id": "path_a_packages",
            "name": "Website · online bestellen",
            "description": "Fertige Landing Page für Ihren Betrieb — Zahlung und Lieferung online.",
            "items": website_items,
        },
    )

    for svc in ONE_TIME_SERVICES:
        sid = str(svc["id"])
        if sid == SERVICE_WEBSITE:
            continue
        online = bool(svc.get("online"))
        categories.append(
            {
                "id": sid,
                "name": svc["customer_name_ru"],
                "description": svc["description_ru"],
                "items": [
                    {
                        "id": sid,
                        "name": svc["name"],
                        "price_label": "скоро" if not online else "по запросу",
                        "timeline": "—",
                        "includes": [],
                        "description": (
                            "Тот же путь: диалог → концепция → согласование → выбор"
                            if not online
                            else "Доступно в диалоге с Vector"
                        ),
                        "cta": "Обсудить с Vector" if online else "Скоро",
                        "cta_href": "/site",
                        "available": online,
                        "tier": "vector" if online else "horizon",
                    }
                ],
            }
        )
    return categories


def build_mission1_vector_commerce_rules(packages: list[dict[str, Any]] | None = None) -> str:
    """Mission 1 commerce block — injected into Vector system prompt and knowledge."""
    pkgs = packages if packages is not None else _landing_packages()
    packages_block = format_order_packages_block(pkgs)
    platform = load_public_pricing_display().get("platform_status") or {}
    studio_note = platform.get("body") or studio_unavailable_message()
    online_services = [s["customer_name_ru"] for s in ONE_TIME_SERVICES if s.get("online")]
    horizon_services = [s["customer_name_ru"] for s in ONE_TIME_SERVICES if not s.get("online")]

    return f"""## Mission 1 — универсальная модель услуг (единая правда)

{platform_directive_v2_rules()}

{universal_service_model_rules()}

{market_detection_rules_for_vector()}

{full_localization_rules_for_vector()}

{global_pricing_rules_for_vector()}

{market_intelligence_rules_for_vector()}

{legal_trust_rules_for_vector()}

{project_platform_rules_for_vector()}

{delivery_rules_for_truth()}

**Сейчас онлайн (разовая услуга):** {", ".join(online_services) or "—"}

**Пакеты сайта на /order (операционные EUR, Mission 1 checkout):**
{packages_block}

**Срок сайта:** ориентир **{MISSION1_LANDING_TIMELINE}** после оплаты и сбора данных.

**{STUDIO_NAME} (подписка):** {studio_note}

**Скоро в каталоге:** {", ".join(horizon_services[:6])}{"…" if len(horizon_services) > 6 else ""}

**Оплата любой услуги:** только после согласования результата; в диалоге — рыночная смета, на `/order` — пакеты.

**Не путать:** услуга = готовый результат. Professional = подписка (этап роста, не скидка)."""


def build_truth_pricing_display(market_code: str | None = None) -> dict:
    from app.integration.commerce_engine import resolve_checkout_packages
    from app.integration.pilot_service_catalog import public_go_to_market
    from app.integration.outreach_market_config import list_markets

    code = (market_code or "DE").strip().upper() or "DE"
    deliverables = {k: v["deliverables"] for k, v in SALES_PACKAGES.items()}
    names = {k: v["name"] for k, v in SALES_PACKAGES.items()}
    checkout = resolve_checkout_packages(
        code,
        deliverables_by_id=deliverables,
        names_by_id=names,
    )
    packages = checkout["packages"]
    currency = str(checkout.get("currency") or "EUR")
    symbol = str(checkout.get("symbol") or "€")
    resolved = str(checkout.get("market_code") or code)
    min_label = packages[0].get("price_label") if packages else f"350 {symbol}"
    for p in packages:
        if p.get("id") == "basic":
            min_label = p.get("price_label") or min_label
            break

    market_rows = []
    for m in list_markets(enabled_only=True):
        mcode = str(m.get("code") or "").upper()
        try:
            snap = resolve_checkout_packages(
                mcode,
                deliverables_by_id=deliverables,
                names_by_id=names,
            )
            basic = next((x for x in snap["packages"] if x["id"] == "basic"), None)
            market_rows.append(
                {
                    "code": mcode,
                    "flag": m.get("flag") or "",
                    "name_en": m.get("name_en") or mcode,
                    "name_ru": m.get("name_ru") or mcode,
                    "currency": snap.get("currency"),
                    "symbol": snap.get("symbol"),
                    "basic_price_label": (basic or {}).get("price_label"),
                }
            )
        except Exception:
            continue

    return {
        "version": TRUTH_VERSION,
        "market_code": resolved,
        "currency": currency,
        "symbol": symbol,
        "markets": market_rows,
        "disclaimer": {
            "ru": (
                f"**Любая услуга** Virtus Core: диалог → концепция → согласование → разовая покупка или подписка. "
                f"Цены для рынка **{resolved}** в {currency} ({symbol}). "
                f"Сайт на /order?market={resolved} от {min_label}; подписка ({STUDIO_NAME}) — в разработке."
            ),
        },
        "platform_status": {
            "label": f"{STUDIO_NAME} — подписка, в разработке",
            "body": (
                f"Подписка — следующий этап роста цифровой компании с {ASSISTANT_NAME}. Пока не продаётся. "
                f"Сейчас: Free (без срока) и разовые услуги (сайт, анализ документов в диалоге)."
            ),
        },
        "service_vs_product": {
            "ru": (
                "**Разовая покупка** = готовый результат и передача проекта. "
                "**Подписка** = проект остаётся в Virtus Core, Vector продолжает работать."
            ),
        },
        "capabilities": None,
        "anti_cannibalization": None,
        "comparison": None,
        "service_categories": _build_service_categories(packages, market_code=resolved),
        "go_to_market": public_go_to_market(),
        "subscriptions": [
            {
                "id": t["id"],
                "name": t["name"],
                "price_eur_month": t.get("price_eur_month"),
                "price_label": (
                    f"{int(t.get('price_eur_month') or 0)} {symbol}"
                    if t.get("price_set") and t.get("price_eur_month") is not None
                    else "скоро"
                ),
                "period": "/мес",
                "audience": t["growth_stage_ru"],
                "tagline": t["tagline_ru"],
                "features": [t["description_ru"]],
                "cta": "Начать работу" if t["available"] else "Coming Soon",
                "cta_href": "/site" if t["available"] else "/products",
                "available": t["available"],
            }
            for t in SUBSCRIPTION_TIERS
        ],
        "services": [],
        "business_units": [],
    }
