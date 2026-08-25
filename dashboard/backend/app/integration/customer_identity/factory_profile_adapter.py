"""Factory read-adapter — Business Profile SSOT → Factory contacts / interview shape.

Law: Enter once → use everywhere.
Order may carry a legacy `business_interview` blob; that is NOT SSOT.
When a Business Profile exists for the customer, Profile wins for company facts.
The interview dict produced here is a *derived view* for Factory composers only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


SSOT_MARKER = "customer_identity.business_profile"


def profile_dict_to_interview(profile: dict[str, Any]) -> dict[str, Any]:
    """Map Business Profile → business_interview-shaped dict (adapter, not storage)."""
    contacts = profile.get("contacts") if isinstance(profile.get("contacts"), dict) else {}
    address = profile.get("address") if isinstance(profile.get("address"), dict) else {}
    services_raw = profile.get("services") if isinstance(profile.get("services"), list) else []
    top_services: list[str] = []
    for item in services_raw:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name:
                top_services.append(name)
        elif isinstance(item, str) and item.strip():
            top_services.append(item.strip())

    about = str(profile.get("description") or "").strip()
    company = str(profile.get("company_name") or "").strip()
    city = str(address.get("city") or "").strip()
    niche = str(profile.get("niche") or "").strip()

    return {
        "company_name": company,
        "about": about,
        "city": city,
        "top_services": top_services,
        "niche": niche,
        "niche_hint": niche,
        "free_text": about,
        "source": "business_profile_ssot",
        "profile_id": str(profile.get("profile_id") or ""),
        "ssot": SSOT_MARKER,
    }


def profile_dict_to_contact_overlay(profile: dict[str, Any]) -> dict[str, Any]:
    """Fields Factory reads from contacts — Profile is sole company-facts source."""
    contacts = profile.get("contacts") if isinstance(profile.get("contacts"), dict) else {}
    address = profile.get("address") if isinstance(profile.get("address"), dict) else {}
    socials = profile.get("socials") if isinstance(profile.get("socials"), dict) else {}
    media = profile.get("media") if isinstance(profile.get("media"), dict) else {}
    services_raw = profile.get("services") if isinstance(profile.get("services"), list) else []
    services_list: list[str] = []
    advantages: list[str] = []
    for item in services_raw:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            if name:
                services_list.append(name)
            hint = str(item.get("price_hint") or "").strip()
            desc = str(item.get("description") or "").strip()
            if hint or desc:
                advantages.append(" — ".join(p for p in (name, hint or desc) if p))
        elif isinstance(item, str) and item.strip():
            services_list.append(item.strip())

    phone = str(contacts.get("phone") or "").strip()
    whatsapp = str(contacts.get("whatsapp") or phone or "").strip()
    email = str(contacts.get("email") or "").strip()
    website = str(contacts.get("website") or "").strip()
    language = str(profile.get("language") or "de").strip() or "de"
    market = str(profile.get("market") or "DE").strip() or "DE"
    logo = str(media.get("logo_path") or "").strip()

    overlay: dict[str, Any] = {
        "business_name": str(profile.get("company_name") or "").strip(),
        "niche": str(profile.get("niche") or "").strip(),
        "who_is_company": str(profile.get("description") or "").strip(),
        "client_story": str(profile.get("description") or "").strip(),
        "phone": phone,
        "whatsapp": whatsapp,
        "email": email,
        "website": website,
        "city": str(address.get("city") or "").strip(),
        "street": str(address.get("street") or "").strip(),
        "postal_code": str(address.get("postal_code") or "").strip(),
        "country": str(address.get("country") or market).strip(),
        "market_code": market,
        "language": language,
        "ui_lang": language,
        "locale": language,
        "services_list": services_list,
        "socials": {
            k: v
            for k, v in socials.items()
            if k != "other" and isinstance(v, str) and v.strip()
        },
    }
    if advantages:
        overlay["advantages"] = advantages
    if logo:
        overlay["logo_path"] = logo
        # Factory client_assets expects materials list of file refs when present
        overlay.setdefault("materials", [])
        if isinstance(overlay["materials"], list) and logo not in overlay["materials"]:
            overlay["materials"] = list(overlay["materials"]) + [
                {"path": logo, "role": "logo", "source": SSOT_MARKER}
            ]
    # Drop empties so we don't wipe order fields with blank profile slots
    return {k: v for k, v in overlay.items() if v not in ("", None, [], {})}


def load_profile_for_customer(
    memory_dir: Path, customer_id: str
) -> dict[str, Any] | None:
    cid = str(customer_id or "").strip()
    if not cid:
        return None
    from app.integration.customer_identity.store import CustomerIdentityStore

    profile = CustomerIdentityStore(memory_dir).load_business_profile_by_customer(cid)
    return profile.to_dict() if profile else None


def apply_business_profile_to_contacts(
    contacts: dict[str, Any] | None,
    *,
    memory_dir: Path,
    customer_id: str | None = None,
) -> dict[str, Any]:
    """Merge Business Profile into Factory contacts. Profile wins when present.

    Does not create a profile. Does not write order SSOT.
    """
    c = dict(contacts or {})
    cid = str(customer_id or c.get("customer_id") or "").strip()
    if not cid:
        c.setdefault("_business_profile_ssot", {"applied": False, "reason": "no_customer_id"})
        return c

    profile = load_profile_for_customer(memory_dir, cid)
    if not profile:
        c["_business_profile_ssot"] = {
            "applied": False,
            "reason": "profile_missing",
            "customer_id": cid,
            "ssot": SSOT_MARKER,
        }
        return c

    overlay = profile_dict_to_contact_overlay(profile)
    interview = profile_dict_to_interview(profile)
    # Profile is sole company-facts source — overlay wins over order copies
    for key, value in overlay.items():
        c[key] = value
    c["business_interview"] = interview
    c["_business_profile_ssot"] = {
        "applied": True,
        "ssot": SSOT_MARKER,
        "profile_id": str(profile.get("profile_id") or ""),
        "customer_id": cid,
        "company_name": str(profile.get("company_name") or ""),
        "source": str(profile.get("source") or ""),
    }
    return c
