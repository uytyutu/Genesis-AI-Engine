"""Slice 4 — Workspace write-back helpers for Business Profile SSOT."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def website_contacts_to_profile_patch(contacts: dict[str, Any] | None) -> dict[str, Any]:
    """Map Website Control Kontakte fields → Business Profile upsert patch."""
    c = contacts if isinstance(contacts, dict) else {}
    phone = str(c.get("phone") or "").strip()
    whatsapp = str(c.get("whatsapp") or "").strip()
    email = str(c.get("email") or "").strip()
    city = str(c.get("city") or "").strip()
    street = str(c.get("address") or c.get("street") or "").strip()
    patch: dict[str, Any] = {"contacts": {}}
    if phone:
        patch["contacts"]["phone"] = phone
    if whatsapp:
        patch["contacts"]["whatsapp"] = whatsapp
    if email:
        patch["contacts"]["email"] = email
    addr: dict[str, str] = {}
    if city:
        addr["city"] = city
    if street:
        addr["street"] = street
    if addr:
        patch["address"] = addr
    if not patch["contacts"]:
        del patch["contacts"]
    return patch


def profile_to_website_contacts(profile: dict[str, Any] | None) -> dict[str, str]:
    """Map Business Profile → Website content.contacts shape."""
    p = profile if isinstance(profile, dict) else {}
    contacts = p.get("contacts") if isinstance(p.get("contacts"), dict) else {}
    address = p.get("address") if isinstance(p.get("address"), dict) else {}
    return {
        "phone": str(contacts.get("phone") or "").strip(),
        "whatsapp": str(contacts.get("whatsapp") or "").strip(),
        "email": str(contacts.get("email") or "").strip(),
        "city": str(address.get("city") or "").strip(),
        "address": str(address.get("street") or "").strip(),
    }


def writeback_website_contacts(
    *,
    memory_dir: Path,
    customer_id: str,
    contacts: dict[str, Any] | None,
    company_name: str | None = None,
) -> dict[str, Any] | None:
    """Persist Website Kontakte into the single Business Profile SSOT."""
    cid = str(customer_id or "").strip()
    if not cid:
        return None
    patch = website_contacts_to_profile_patch(contacts)
    name = str(company_name or "").strip()
    if name:
        patch["company_name"] = name
    if not patch:
        return None
    from app.integration.customer_identity.service import CustomerIdentityService

    return CustomerIdentityService(memory_dir).upsert_business_profile(
        cid, patch, source="website_admin"
    )


def sync_profile_contacts_to_website_orders(
    *,
    memory_dir: Path,
    customer_id: str,
    profile: dict[str, Any],
) -> int:
    """Push Profile contacts into content.json of owned website orders (no second SSOT)."""
    cid = str(customer_id or "").strip()
    if not cid:
        return 0
    from app.integration.sales_order_service import SalesOrderService
    from app.integration.website_admin.content_service import WebsiteContentService

    # Lightweight factory stub not needed — list orders via SalesOrderService file only
    try:
        from app.factory.factory_service import FactoryService
        from app.integration.factory_intent_service import FactoryIntentService

        factory = FactoryService(memory_dir=memory_dir)
        intent = FactoryIntentService(memory_dir=memory_dir, factory=factory)
        sales = SalesOrderService(memory_dir, intent)
        orders = sales.list_orders_for_customer(customer_id=cid, limit=50)
    except Exception:
        return 0

    contacts = profile_to_website_contacts(profile)
    company = str(profile.get("company_name") or "").strip()
    svc = WebsiteContentService(memory_dir)
    updated = 0
    for order in orders:
        oid = str(order.get("order_id") or "").strip()
        kind = str(order.get("product_kind") or order.get("package_id") or "").lower()
        if not oid:
            continue
        if "store" in kind or "shop" in kind or "bot" in kind:
            continue
        try:
            payload: dict[str, Any] = {"contacts": contacts}
            if company:
                # Keep hero title aligned when it looks like a company name slot
                current = svc.raw_content(oid)
                hero = current.get("hero") if isinstance(current.get("hero"), dict) else {}
                if not str(hero.get("title") or "").strip() or str(hero.get("title")) != company:
                    payload["hero"] = {**hero, "title": company}
            svc.update_content(oid, payload, record_history=True)
            updated += 1
        except Exception:
            continue
    return updated
