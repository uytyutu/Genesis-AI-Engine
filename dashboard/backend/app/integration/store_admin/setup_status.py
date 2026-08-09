"""Vector Phase 1 — Store Admin setup readiness (rule-based, no LLM).

One contextual assistant surface: checklist + % + tips with deep-links.
Commerce provider steps stay honest stubs until R3.3.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.store_admin.catalog_service import StoreCatalogService
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.store_admin.design_service import (
    StoreDesignService,
    default_design,
)

PRODUCT_TARGET = 10
SURFACE = "store_admin"


def _connected(status: Any) -> bool:
    return str(status or "").lower() in {
        "connected",
        "active",
        "enabled",
        "ready",
    }


def _has_logo(design: dict[str, Any]) -> bool:
    branding = design.get("branding") if isinstance(design.get("branding"), dict) else {}
    logo = branding.get("logo")
    return isinstance(logo, dict) and bool(logo.get("id") or logo.get("url"))


def _colors_customized(design: dict[str, Any]) -> bool:
    defaults = default_design()["colors"]
    colors = design.get("colors") if isinstance(design.get("colors"), dict) else {}
    for key, default_val in defaults.items():
        if str(colors.get(key) or "").lower() != str(default_val).lower():
            return True
    branding = design.get("branding") if isinstance(design.get("branding"), dict) else {}
    if str(branding.get("tagline") or "").strip():
        return True
    typo = design.get("typography") if isinstance(design.get("typography"), dict) else {}
    if str(typo.get("font_preset") or "") not in ("", "dm_fraunces"):
        return True
    return bool(design.get("updated_at"))


def _any_shipping_connected(settings: dict[str, Any]) -> bool:
    shipping = settings.get("shipping") if isinstance(settings.get("shipping"), dict) else {}
    return any(
        isinstance(row, dict) and _connected(row.get("status"))
        for row in shipping.values()
    )


def build_setup_status(
    *,
    order_id: str,
    product_count: int,
    design: dict[str, Any],
    commerce_settings: dict[str, Any],
    shop_pipeline: str | None = None,
    customer_count: int = 0,
    order_count: int = 0,
) -> dict[str, Any]:
    """Pure readiness builder — easy to unit-test without filesystem."""
    logo_ok = _has_logo(design)
    products_ok = product_count >= 1
    catalog_strong = product_count >= PRODUCT_TARGET
    colors_ok = _colors_customized(design)

    payments = (
        commerce_settings.get("payments")
        if isinstance(commerce_settings.get("payments"), dict)
        else {}
    )
    stripe = payments.get("stripe") if isinstance(payments.get("stripe"), dict) else {}
    paypal = payments.get("paypal") if isinstance(payments.get("paypal"), dict) else {}
    taxes = (
        commerce_settings.get("taxes")
        if isinstance(commerce_settings.get("taxes"), dict)
        else {}
    )

    stripe_ok = _connected(stripe.get("status"))
    paypal_ok = _connected(paypal.get("status"))
    shipping_ok = _any_shipping_connected(commerce_settings)
    taxes_ok = _connected(taxes.get("status"))
    email_block = (
        commerce_settings.get("email")
        if isinstance(commerce_settings.get("email"), dict)
        else {}
    )
    email_ok = any(
        isinstance(row, dict) and _connected(row.get("status"))
        for row in email_block.values()
    )
    transport = (
        commerce_settings.get("email_transport")
        if isinstance(commerce_settings.get("email_transport"), dict)
        else {}
    )
    last_test = (
        transport.get("last_test") if isinstance(transport.get("last_test"), dict) else {}
    )
    email_tested = bool(last_test.get("ok"))
    published = str(shop_pipeline or "").lower() in {"published", "live"}

    steps: list[dict[str, Any]] = [
        {
            "id": "logo",
            "label": "Logo",
            "done": logo_ok,
            "actionable": True,
            "weight": 15,
            "section": "design",
            "cta_label": "Upload logo",
        },
        {
            "id": "products",
            "label": "Products",
            "done": products_ok,
            "actionable": True,
            "weight": 18,
            "section": "products",
            "cta_label": "Add products",
            "meta": {
                "count": product_count,
                "target": PRODUCT_TARGET,
                "strong": catalog_strong,
            },
        },
        {
            "id": "colors",
            "label": "Colors",
            "done": colors_ok,
            "actionable": True,
            "weight": 10,
            "section": "design",
            "cta_label": "Edit brand colors",
        },
        {
            "id": "stripe",
            "label": "Stripe",
            "done": stripe_ok,
            "actionable": True,
            "weight": 12,
            "section": "payments",
            "cta_label": "Connect Stripe",
        },
        {
            "id": "paypal",
            "label": "PayPal",
            "done": paypal_ok,
            "actionable": True,
            "weight": 8,
            "section": "payments",
            "cta_label": "Connect PayPal",
        },
        {
            "id": "shipping",
            "label": "Shipping",
            "done": shipping_ok,
            "actionable": True,
            "weight": 10,
            "section": "shipping",
            "cta_label": "Настроить",
        },
        {
            "id": "email",
            "label": "Email",
            "done": email_ok and email_tested,
            "actionable": True,
            "weight": 10,
            "section": "email",
            "cta_label": "Connect Email" if not email_ok else "Send Test Email",
            "meta": {"connected": email_ok, "tested": email_tested},
        },
        {
            "id": "taxes",
            "label": "Taxes",
            "done": taxes_ok,
            "actionable": True,
            "weight": 8,
            "section": "commerce",
            "cta_label": "Configure VAT",
        },
        {
            "id": "publish",
            "label": "Publish",
            "done": published,
            "actionable": True,
            "weight": 9,
            "section": "dashboard",
            "cta_label": "Publish store",
        },
    ]

    total_w = sum(int(s["weight"]) for s in steps) or 1
    earned = sum(int(s["weight"]) for s in steps if s["done"])
    readiness_pct = int(round(100 * earned / total_w))

    actionable = [s for s in steps if s["actionable"]]
    actionable_w = sum(int(s["weight"]) for s in actionable) or 1
    actionable_earned = sum(int(s["weight"]) for s in actionable if s["done"])
    setup_pct = int(round(100 * actionable_earned / actionable_w))

    tips = _build_tips(
        product_count=product_count,
        logo_ok=logo_ok,
        colors_ok=colors_ok,
        stripe_ok=stripe_ok,
        shipping_ok=shipping_ok,
        published=published,
        catalog_strong=catalog_strong,
        commerce_settings=commerce_settings,
    )

    next_step = next((s for s in steps if s["actionable"] and not s["done"]), None)
    if next_step is None:
        next_step = next((s for s in steps if not s["done"]), None)

    greeting = (
        "Welcome. Your AI Store is ready to configure — let's finish setup together."
        if readiness_pct < 100
        else "Nice work. Your store checklist is complete — keep catalog and commerce fresh."
    )

    return {
        "ok": True,
        "order_id": order_id,
        "surface": SURFACE,
        "vector": {
            "assistant": "Vector",
            "mode": "setup_guidance",
            "greeting": greeting,
        },
        "readiness_pct": readiness_pct,
        "setup_pct": setup_pct,
        "product_count": product_count,
        "customer_count": customer_count,
        "order_count": order_count,
        "shop_pipeline": shop_pipeline,
        "steps": steps,
        "next_step": next_step,
        "tips": tips,
        "commerce_ready": stripe_ok or paypal_ok,
        "note": "Rule-based Vector guidance. Commerce R3.3 Payments–Notifications live.",
    }


def _build_tips(
    *,
    product_count: int,
    logo_ok: bool,
    colors_ok: bool,
    stripe_ok: bool,
    shipping_ok: bool,
    published: bool,
    catalog_strong: bool,
    commerce_settings: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    tips: list[dict[str, Any]] = []
    if commerce_settings:
        try:
            from app.integration.store_admin.commerce_settings import shipping_guidance

            tips.extend(shipping_guidance(commerce_settings))
        except Exception:
            pass
    if not logo_ok:
        tips.append(
            {
                "id": "tip_logo",
                "priority": 10,
                "message": "Upload a logo so buyers recognize your brand on every page.",
                "section": "design",
                "cta_label": "Upload logo",
            }
        )
    if product_count == 0:
        tips.append(
            {
                "id": "tip_products_empty",
                "priority": 20,
                "message": "Add your first product — a store without a catalog can't sell.",
                "section": "products",
                "cta_label": "Add product",
            }
        )
    elif not catalog_strong:
        tips.append(
            {
                "id": "tip_products_thin",
                "priority": 25,
                "message": (
                    f"You have only {product_count} product"
                    f"{'' if product_count == 1 else 's'}. "
                    f"I recommend adding at least {PRODUCT_TARGET}."
                ),
                "section": "products",
                "cta_label": "Add more products",
            }
        )
    if not colors_ok:
        tips.append(
            {
                "id": "tip_colors",
                "priority": 30,
                "message": "Tune brand colors so the shopfront matches your identity.",
                "section": "design",
                "cta_label": "Open Design",
            }
        )
    if not stripe_ok:
        tips.append(
            {
                "id": "tip_stripe",
                "priority": 40,
                "message": "Stripe is not connected yet. Connect your own Stripe account in Payments.",
                "section": "payments",
                "cta_label": "Connect Stripe",
            }
        )
    # shipping tips come from shipping_guidance when commerce_settings present
    if not shipping_ok and not commerce_settings:
        tips.append(
            {
                "id": "tip_shipping",
                "priority": 50,
                "message": "Подключите DHL или самовывоз в Shipping.",
                "section": "shipping",
                "cta_label": "Настроить",
            }
        )
    if not published and product_count > 0 and logo_ok:
        tips.append(
            {
                "id": "tip_publish",
                "priority": 60,
                "message": "Catalog looks started — publish when you're happy with the storefront.",
                "section": "dashboard",
                "cta_label": "Check publish status",
            }
        )
    tips.sort(key=lambda t: int(t.get("priority") or 99))
    return tips


class StoreSetupStatusService:
    """Aggregate catalog + design + commerce stubs into Vector setup context."""

    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._catalog = StoreCatalogService(self._memory)
        self._design = StoreDesignService(self._memory)
        self._commerce = StoreCommerceSettingsService(self._memory)

    def get(
        self,
        order_id: str,
        *,
        store_name: str = "",
        shop_pipeline: str | None = None,
        customer_count: int = 0,
        order_count: int = 0,
    ) -> dict[str, Any]:
        listed = self._catalog.list_products(order_id)
        design_payload = self._design.get_design(order_id, store_name=store_name)
        design = design_payload.get("design") or {}
        commerce = self._commerce.ensure_saved(order_id)
        settings = commerce.get("settings") or {}
        return build_setup_status(
            order_id=order_id,
            product_count=int(listed.get("count") or 0),
            design=design if isinstance(design, dict) else {},
            commerce_settings=settings if isinstance(settings, dict) else {},
            shop_pipeline=shop_pipeline,
            customer_count=customer_count,
            order_count=order_count,
        )
