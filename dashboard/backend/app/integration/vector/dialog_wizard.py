"""Vector Dialog Wizard — rule-based turns with action buttons (not ChatGPT clone).

One Vector, many surfaces. Dialog dock opens right/bottom; steps deep-link into UI.
"""

from __future__ import annotations

from typing import Any

from app.integration.vector.capabilities import action_for, coming_label, is_live
from app.integration.vector.business_setup import build_business_setup

PRODUCT_TARGET = 10

# Ordered wizard steps for store_admin (matches merchant setup path).
STORE_WIZARD: list[dict[str, Any]] = [
    {
        "id": "welcome",
        "kind": "intro",
        "done_when": lambda ctx: False,  # always show once at start; skip via cursor
    },
    {
        "id": "logo",
        "capability": "store_design_logo",
        "done_key": "logo_ok",
    },
    {
        "id": "products",
        "capability": "store_products",
        "done_key": "products_ok",
    },
    {
        "id": "colors",
        "capability": "store_design_colors",
        "done_key": "colors_ok",
    },
    {
        "id": "stripe",
        "capability": "payments_stripe",
        "done_key": "stripe_ok",
    },
    {
        "id": "shipping",
        "capability": "shipping_carriers",
        "done_key": "shipping_ok",
    },
    {
        "id": "email",
        "capability": "email_transactional",
        "done_key": "email_ok",
    },
    {
        "id": "publish",
        "capability": "store_publish",
        "done_key": "published",
    },
    {
        "id": "complete",
        "kind": "finale",
    },
]


def _msg(role: str, text: str, **extra: Any) -> dict[str, Any]:
    row = {"role": role, "text": text}
    row.update(extra)
    return row


def _store_flags(setup: dict[str, Any]) -> dict[str, Any]:
    steps = {s["id"]: s for s in setup.get("steps") or [] if isinstance(s, dict)}
    product_count = int(setup.get("product_count") or 0)
    return {
        "logo_ok": bool((steps.get("logo") or {}).get("done")),
        "products_ok": bool((steps.get("products") or {}).get("done")),
        "colors_ok": bool((steps.get("colors") or {}).get("done")),
        "stripe_ok": bool((steps.get("stripe") or {}).get("done")),
        "shipping_ok": bool((steps.get("shipping") or {}).get("done")),
        "email_ok": bool((steps.get("email") or {}).get("done")),
        "published": bool((steps.get("publish") or {}).get("done")),
        "product_count": product_count,
        "catalog_strong": product_count >= PRODUCT_TARGET,
        "readiness_pct": int(setup.get("readiness_pct") or 0),
        "order_id": setup.get("order_id"),
        "store_name": setup.get("store_name") or "your store",
    }


def _resolve_wizard_index(flags: dict[str, Any], *, prefer_id: str | None = None) -> int:
    if prefer_id:
        for i, step in enumerate(STORE_WIZARD):
            if step["id"] == prefer_id:
                return i
    # Skip welcome after first open is handled client-side; server picks first incomplete
    for i, step in enumerate(STORE_WIZARD):
        if step.get("kind") == "intro":
            continue
        if step.get("kind") == "finale":
            return i
        key = step.get("done_key")
        if key and not flags.get(key):
            return i
    return len(STORE_WIZARD) - 1


def build_store_dialog(
    setup: dict[str, Any],
    *,
    learning_mode: str | None = None,
    step_id: str | None = None,
    include_welcome: bool = True,
) -> dict[str, Any]:
    """Build docked dialog payload for Store Admin."""
    flags = _store_flags(setup)
    order_id = str(flags.get("order_id") or setup.get("order_id") or "")

    if learning_mode is None:
        # First prompt: learn vs work
        return {
            "ok": True,
            "surface": "store_admin",
            "assistant": "Vector",
            "mode": "learning_gate",
            "dock": "right",
            "messages": [
                _msg(
                    "assistant",
                    "Welcome! Today we'll set up your store — about 10 minutes.\n\n"
                    "Would you like a quick walkthrough (1–2 min) or jump straight to work?",
                )
            ],
            "actions": [
                {
                    "id": "learn_skip",
                    "kind": "set_learning",
                    "value": "skip",
                    "label": "Straight to work",
                    "status": "live",
                },
                {
                    "id": "learn_show",
                    "kind": "set_learning",
                    "value": "show",
                    "label": "Show training",
                    "status": "live",
                },
            ],
            "wizard": None,
            "setup_pct": setup.get("setup_pct"),
            "readiness_pct": setup.get("readiness_pct"),
            "honesty": "Vector never offers features that are not live yet.",
        }

    idx = _resolve_wizard_index(flags, prefer_id=step_id)
    if include_welcome and step_id is None and learning_mode == "show":
        # Start at welcome when training mode
        idx = 0
    elif step_id is None and learning_mode == "skip":
        idx = _resolve_wizard_index(flags)

    step = STORE_WIZARD[idx]
    messages: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    if step.get("kind") == "intro":
        messages.append(
            _msg(
                "assistant",
                "Welcome! Today we'll fully set up your store. This takes about 10 minutes.\n\n"
                "I'll guide you step by step — each step has a button.",
            )
        )
        if learning_mode == "show":
            messages.append(
                _msg(
                    "assistant",
                    "Training tip: complete Logo → Products → Colors first. "
                    "Payments and shipping arrive in Commerce R3.3 — I'll say so honestly.",
                )
            )
        actions.append(
            {
                "id": "wizard_next",
                "kind": "wizard_goto",
                "step_id": "logo",
                "label": "Start with logo",
                "status": "live",
            }
        )
    elif step.get("kind") == "finale":
        messages.append(
            _msg(
                "assistant",
                "Congratulations! Your store checklist is complete for everything available today.\n\n"
                f"Store readiness: {flags['readiness_pct']}%. "
                "Keep Payments, Shipping and Taxes fresh in Integrations.",
            )
        )
        actions.append(
            action_for("store_products", cta_override="Review products")
        )
    else:
        cap = str(step.get("capability") or "")
        sid = step["id"]
        done = bool(flags.get(step.get("done_key") or ""))

        if sid == "logo":
            if done:
                messages.append(
                    _msg(
                        "assistant",
                        "Logo looks good — your shop already feels more professional.",
                    )
                )
                actions.append(
                    {
                        "id": "wizard_next",
                        "kind": "wizard_goto",
                        "step_id": "products",
                        "label": "Next: products",
                        "status": "live",
                    }
                )
            else:
                messages.append(
                    _msg("assistant", "Step 1 — Upload your logo.")
                )
                actions.append(
                    action_for("store_design_logo", cta_override="Upload logo")
                )
        elif sid == "products":
            count = int(flags["product_count"])
            if count == 0:
                messages.append(
                    _msg(
                        "assistant",
                        "Step 2 — Add your first products.\n\n"
                        "A store without a catalog can't sell.",
                    )
                )
            elif not flags["catalog_strong"]:
                messages.append(
                    _msg(
                        "assistant",
                        f"Step 2 — Products\n\n"
                        f"You currently have **{count}** product"
                        f"{'' if count == 1 else 's'}.\n"
                        f"For a stronger first impression I recommend at least "
                        f"**{PRODUCT_TARGET}**.",
                    )
                )
            else:
                messages.append(
                    _msg(
                        "assistant",
                        f"Great catalog — {count} products. Nice work.",
                    )
                )
            if is_live(cap):
                actions.append(
                    action_for("store_products", cta_override="Open Products")
                )
            if count >= 1:
                actions.append(
                    {
                        "id": "wizard_next",
                        "kind": "wizard_goto",
                        "step_id": "colors",
                        "label": "Next: colors",
                        "status": "live",
                    }
                )
        elif sid == "colors":
            if done:
                messages.append(
                    _msg("assistant", "Brand colors are set. Looking sharper already.")
                )
                actions.append(
                    {
                        "id": "wizard_next",
                        "kind": "wizard_goto",
                        "step_id": "stripe",
                        "label": "Next",
                        "status": "live",
                    }
                )
            else:
                messages.append(
                    _msg("assistant", "Step 3 — Tune your brand colors.")
                )
                actions.append(
                    action_for("store_design_colors", cta_override="Open Design")
                )
        elif sid == "stripe":
            if done:
                messages.append(
                    _msg(
                        "assistant",
                        "Stripe is connected to your merchant account. "
                        "Virtus Core never takes buyer funds.",
                    )
                )
                actions.append(
                    {
                        "id": "wizard_next",
                        "kind": "wizard_goto",
                        "step_id": "shipping",
                        "label": "Continue",
                        "status": "live",
                    }
                )
            else:
                messages.append(
                    _msg(
                        "assistant",
                        "Step 4 — Connect Stripe.\n\n"
                        "Use your own Stripe account in Payments. "
                        "Virtus Core does not receive customer payments.",
                    )
                )
                actions.append(
                    action_for("payments_stripe", cta_override="Connect Stripe")
                )
                actions.append(
                    {
                        "id": "wizard_next",
                        "kind": "wizard_goto",
                        "step_id": "shipping",
                        "label": "Skip for now",
                        "status": "live",
                    }
                )
        elif sid == "shipping":
            if done:
                messages.append(
                    _msg(
                        "assistant",
                        "✅ Доставка настроена.\n\n"
                        "Можно уточнить бесплатную доставку от суммы заказа в Shipping.",
                    )
                )
            else:
                messages.append(
                    _msg(
                        "assistant",
                        "Step 5 — Настройте доставку.\n\n"
                        "Подключите DHL, DPD, GLS, Hermes, UPS, FedEx или самовывоз. "
                        "У вас не настроена бесплатная доставка? Можно добавить от 100 €.",
                    )
                )
            actions.append(
                action_for("shipping_carriers", cta_override="Настроить")
            )
            actions.append(
                {
                    "id": "wizard_next",
                    "kind": "wizard_goto",
                    "step_id": "email",
                    "label": "Continue",
                    "status": "live",
                }
            )
        elif sid == "email":
            if done:
                messages.append(
                    _msg(
                        "assistant",
                        "✅ Email успешно подключён.\n\n"
                        "Хотите отправить тестовое письмо?",
                    )
                )
                actions.append(
                    {
                        "id": "email_test",
                        "kind": "navigate_section",
                        "section": "email",
                        "label": "Send Test Email",
                        "status": "live",
                    }
                )
            else:
                messages.append(
                    _msg(
                        "assistant",
                        "Step 6 — Connect Email (Gmail / Outlook / Microsoft 365 / SMTP).\n\n"
                        "После подключения нажмите Send Test Email — "
                        "так вы сразу увидите, работает ли доставка писем.",
                    )
                )
                actions.append(
                    action_for("email_transactional", cta_override="Connect Email")
                )
            actions.append(
                {
                    "id": "wizard_next",
                    "kind": "wizard_goto",
                    "step_id": "publish",
                    "label": "Continue",
                    "status": "live",
                }
            )
        elif sid == "publish":
            if done:
                messages.append(
                    _msg(
                        "assistant",
                        "Your store is published. You're ready for customers.",
                    )
                )
                actions.append(
                    {
                        "id": "wizard_next",
                        "kind": "wizard_goto",
                        "step_id": "complete",
                        "label": "Finish",
                        "status": "live",
                    }
                )
            else:
                messages.append(
                    _msg(
                        "assistant",
                        "Step 6 — Publish your store when the catalog and branding look right.",
                    )
                )
                actions.append(
                    action_for("store_publish", cta_override="Check publish status")
                )

    wizard = {
        "step_id": step["id"],
        "index": idx + 1,
        "total": len(STORE_WIZARD),
        "steps": [
            {
                "id": s["id"],
                "done": (
                    True
                    if s.get("kind") == "finale"
                    and all(
                        flags.get(x.get("done_key"))
                        for x in STORE_WIZARD
                        if x.get("done_key") and is_live(str(x.get("capability") or ""))
                    )
                    else bool(flags.get(s.get("done_key") or ""))
                    if s.get("done_key")
                    else s.get("kind") == "intro"
                ),
                "coming": coming_label(str(s.get("capability") or ""))
                if s.get("capability") and not is_live(str(s.get("capability")))
                else None,
            }
            for s in STORE_WIZARD
            if s.get("kind") != "intro" and s.get("kind") != "finale"
        ],
    }

    return {
        "ok": True,
        "surface": "store_admin",
        "assistant": "Vector",
        "mode": "dialog_wizard",
        "dock": "right",
        "learning_mode": learning_mode,
        "messages": messages,
        "actions": actions,
        "wizard": wizard,
        "setup_pct": setup.get("setup_pct"),
        "readiness_pct": setup.get("readiness_pct"),
        "honesty": "Vector never offers features that are not live yet.",
    }


def build_platform_dialog(
    *,
    has_store: bool,
    store_order_id: str | None,
    store_name: str | None,
    has_website: bool,
    business_setup: dict[str, Any] | None = None,
    learning_mode: str | None = "skip",
) -> dict[str, Any]:
    messages: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    if has_store and store_order_id:
        name = store_name or "your AI Store"
        messages.append(
            _msg(
                "assistant",
                f"Thank you for ordering {name}.\n\n"
                "Next step — open Store Admin. I'll guide logo, products, colors, "
                "and tell you honestly what waits for Commerce R3.3.",
            )
        )
        actions.append(
            action_for(
                "open_store_admin",
                order_id=store_order_id,
                cta_override="Open Store Admin",
            )
        )
    elif has_website:
        messages.append(
            _msg(
                "assistant",
                "Welcome back. Your website is in the workspace.\n\n"
                "Website Admin tips (Impressum, Maps, SEO) arrive next — "
                "Coming R3.2. For now you can review products and orders.",
            )
        )
        actions.append(action_for("open_products", cta_override="My products"))
    else:
        messages.append(
            _msg(
                "assistant",
                "Welcome to Virtus Core.\n\n"
                "Start with a website or AI Store — I'll guide setup after purchase.",
            )
        )
        actions.append(
            {
                "id": "order_website",
                "kind": "navigate_href",
                "href": "/order",
                "label": "Order website",
                "status": "live",
            }
        )
        actions.append(
            {
                "id": "order_store",
                "kind": "navigate_href",
                "href": "/order/shop",
                "label": "Order AI Store",
                "status": "live",
            }
        )

    if business_setup and business_setup.get("next"):
        nxt = business_setup["next"]
        if not nxt.get("done"):
            messages.append(
                _msg(
                    "assistant",
                    f"Business Setup is at **{business_setup.get('pct', 0)}%**. "
                    f"Next focus: {nxt.get('label')}.",
                )
            )

    return {
        "ok": True,
        "surface": "platform",
        "assistant": "Vector",
        "mode": "dialog_wizard",
        "dock": "right",
        "learning_mode": learning_mode,
        "messages": messages,
        "actions": actions,
        "wizard": None,
        "business_setup": business_setup,
        "honesty": "Vector never offers features that are not live yet.",
    }


def build_website_dialog_stub() -> dict[str, Any]:
    """Website Admin context — honest Coming until R3.2 tips ship."""
    return {
        "ok": True,
        "surface": "website_admin",
        "assistant": "Vector",
        "mode": "dialog_wizard",
        "dock": "right",
        "messages": [
            _msg(
                "assistant",
                "Website Admin guidance is next.\n\n"
                "I'll check Impressum, Datenschutz, Maps and meta description — "
                "**Coming R3.2**. I won't invent Create buttons that don't work yet.",
            )
        ],
        "actions": [
            action_for("website_impressum"),
            action_for("website_maps"),
            action_for("website_meta"),
        ],
        "wizard": None,
        "honesty": "Vector never offers features that are not live yet.",
    }


def build_customer_dialog_stub() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "customer",
        "assistant": "Vector",
        "mode": "dialog_wizard",
        "dock": "bottom",
        "messages": [
            _msg(
                "assistant",
                "Customer Account help is preparing.\n\n"
                "For now you can browse the shop and your orders — "
                "full guided help is Coming soon.",
            )
        ],
        "actions": [],
        "wizard": None,
        "honesty": "Vector never offers features that are not live yet.",
    }


# re-export for services
__all__ = [
    "build_store_dialog",
    "build_platform_dialog",
    "build_website_dialog_stub",
    "build_customer_dialog_stub",
    "build_business_setup",
    "PRODUCT_TARGET",
]
