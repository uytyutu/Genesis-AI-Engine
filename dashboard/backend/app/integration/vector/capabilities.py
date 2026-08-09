"""Vector honesty registry — never offer what the system cannot do yet.

Rule: if a capability is not live, Vector must say Coming R{x} and must not
simulate Connect / Create success.
"""

from __future__ import annotations

from typing import Any

# status: live | coming | stub
CAPABILITIES: dict[str, dict[str, Any]] = {
    "store_design_logo": {
        "status": "live",
        "label": "Upload logo",
        "surface": "store_admin",
        "section": "design",
    },
    "store_products": {
        "status": "live",
        "label": "Manage products",
        "surface": "store_admin",
        "section": "products",
    },
    "store_design_colors": {
        "status": "live",
        "label": "Brand colors",
        "surface": "store_admin",
        "section": "design",
    },
    "store_publish": {
        "status": "live",
        "label": "Publish store",
        "surface": "store_admin",
        "section": "dashboard",
    },
    "store_customers": {
        "status": "live",
        "label": "Customers",
        "surface": "store_admin",
        "section": "customers",
    },
    "payments_stripe": {
        "status": "live",
        "label": "Connect Stripe",
        "surface": "store_admin",
        "section": "payments",
    },
    "payments_paypal": {
        "status": "live",
        "label": "Connect PayPal",
        "surface": "store_admin",
        "section": "payments",
    },
    "shipping_carriers": {
        "status": "live",
        "label": "Настроить доставку",
        "surface": "store_admin",
        "section": "shipping",
    },
    "taxes_vat": {
        "status": "live",
        "label": "Configure VAT",
        "surface": "store_admin",
        "section": "commerce",
    },
    "email_transactional": {
        "status": "live",
        "label": "Connect Email",
        "surface": "store_admin",
        "section": "email",
    },
    "invoices_pdf": {
        "status": "live",
        "label": "Invoice settings",
        "surface": "store_admin",
        "section": "integrations",
    },
    "notifications_channels": {
        "status": "live",
        "label": "Notifications",
        "surface": "store_admin",
        "section": "integrations",
    },
    "analytics": {
        "status": "coming",
        "coming": "R3.4",
        "label": "Analytics",
        "surface": "store_admin",
        "section": "analytics",
    },
    "marketing": {
        "status": "coming",
        "coming": "R3.4",
        "label": "Marketing",
        "surface": "store_admin",
        "section": "marketing",
    },
    "website_impressum": {
        "status": "coming",
        "coming": "R3.2",
        "label": "Create Impressum",
        "surface": "website_admin",
        "section": "support",
    },
    "website_maps": {
        "status": "coming",
        "coming": "R3.2",
        "label": "Add Google Maps",
        "surface": "website_admin",
        "section": "website",
    },
    "website_meta": {
        "status": "coming",
        "coming": "R3.2",
        "label": "Generate meta description",
        "surface": "website_admin",
        "section": "website",
    },
    "website_content_hero": {
        "status": "live",
        "label": "Edit Hero",
        "surface": "website_admin",
        "section": "website",
    },
    "website_content_services": {
        "status": "live",
        "label": "Edit services",
        "surface": "website_admin",
        "section": "website",
    },
    "website_content_contacts": {
        "status": "live",
        "label": "Edit contacts",
        "surface": "website_admin",
        "section": "website",
    },
    "website_design_logo": {
        "status": "live",
        "label": "Upload logo",
        "surface": "website_admin",
        "section": "design",
    },
    "website_design_colors": {
        "status": "live",
        "label": "Brand colors",
        "surface": "website_admin",
        "section": "design",
    },
    "website_ai_edit": {
        "status": "live",
        "label": "AI edit website",
        "surface": "website_admin",
        "section": "ai",
    },
    "website_publish": {
        "status": "live",
        "label": "Publish website",
        "surface": "website_admin",
        "section": "dashboard",
    },
    "open_website_admin": {
        "status": "live",
        "label": "Open Website Control",
        "surface": "platform",
        "href_template": "/client/websites/{order_id}/admin",
    },
    "open_store_admin": {
        "status": "live",
        "label": "Open Store Admin",
        "surface": "platform",
        "href_template": "/client/stores/{order_id}/admin",
    },
    "open_products": {
        "status": "live",
        "label": "My products",
        "surface": "platform",
        "href": "/client/products",
    },
}


def capability(cap_id: str) -> dict[str, Any] | None:
    row = CAPABILITIES.get(cap_id)
    return dict(row) if row else None


def is_live(cap_id: str) -> bool:
    row = CAPABILITIES.get(cap_id) or {}
    return str(row.get("status") or "") == "live"


def coming_label(cap_id: str) -> str | None:
    row = CAPABILITIES.get(cap_id) or {}
    if str(row.get("status") or "") == "coming":
        return str(row.get("coming") or "soon")
    return None


def action_for(
    cap_id: str,
    *,
    cta_override: str | None = None,
    order_id: str | None = None,
) -> dict[str, Any]:
    """Build a Vector action button — live opens UI; coming stays honest."""
    row = capability(cap_id) or {
        "status": "coming",
        "coming": "soon",
        "label": cap_id,
    }
    status = str(row.get("status") or "coming")
    label = cta_override or str(row.get("label") or cap_id)
    action: dict[str, Any] = {
        "id": cap_id,
        "capability": cap_id,
        "label": label,
        "status": status,
    }
    if status == "live":
        if row.get("section"):
            action["kind"] = "navigate_section"
            action["section"] = row["section"]
        elif row.get("href_template") and order_id:
            action["kind"] = "navigate_href"
            action["href"] = str(row["href_template"]).format(order_id=order_id)
        elif row.get("href"):
            action["kind"] = "navigate_href"
            action["href"] = row["href"]
        else:
            action["kind"] = "noop"
    else:
        action["kind"] = "coming"
        action["coming"] = row.get("coming") or "soon"
        action["label"] = f"Coming {action['coming']}"
    return action
