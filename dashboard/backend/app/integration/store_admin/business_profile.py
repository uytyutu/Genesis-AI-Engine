"""Business Profile — single source of truth for merchant contacts.

Used by Website Factory, AI Store, Email, PDF, Contact Forms, Website Admin,
and Store Admin. Change phone/email/address once → everywhere.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PHONE_DIGITS = re.compile(r"[^\d+]")

# Common dial codes for DE SME default + neighbors
COUNTRY_DIAL: dict[str, str] = {
    "DE": "+49",
    "AT": "+43",
    "CH": "+41",
    "NL": "+31",
    "BE": "+32",
    "FR": "+33",
    "PL": "+48",
    "CZ": "+420",
    "IT": "+39",
    "ES": "+34",
    "GB": "+44",
    "US": "+1",
    "UA": "+380",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_business_profile() -> dict[str, Any]:
    return {
        "version": 1,
        "company_name": None,
        "phone_country_code": "DE",
        "phone_primary": None,
        "phone_secondary": None,
        "whatsapp": None,
        "telegram": None,
        "email_support": None,
        "email_orders": None,
        "address": {
            "street": None,
            "postal_code": None,
            "city": None,
            "country": "DE",
        },
        "hours": None,
        "social_links": {
            "instagram": None,
            "facebook": None,
            "linkedin": None,
            "youtube": None,
            "tiktok": None,
            "x": None,
        },
        "logo_asset_id": None,
        "updated_at": None,
    }


def digits_only(phone: str | None) -> str:
    raw = (phone or "").strip()
    if not raw:
        return ""
    # keep leading + for intl, else digits
    cleaned = PHONE_DIGITS.sub("", raw)
    return cleaned


def format_phone_display(phone: str | None, country_code: str = "DE") -> str | None:
    dig = digits_only(phone)
    if not dig:
        return None
    dial = COUNTRY_DIAL.get((country_code or "DE").upper(), "+49")
    if dig.startswith("+"):
        return dig
    # strip leading 0 for national format
    national = dig[1:] if dig.startswith("0") else dig
    return f"{dial} {national}"


def tel_href(phone: str | None, country_code: str = "DE") -> str | None:
    display = format_phone_display(phone, country_code)
    if not display:
        return None
    return "tel:" + PHONE_DIGITS.sub("", display)


def wa_me_href(whatsapp: str | None, country_code: str = "DE") -> str | None:
    dig = digits_only(whatsapp)
    if not dig:
        return None
    if dig.startswith("+"):
        dig = dig[1:]
    elif dig.startswith("0"):
        dial = COUNTRY_DIAL.get((country_code or "DE").upper(), "+49").lstrip("+")
        dig = dial + dig[1:]
    elif not dig.startswith(tuple("123456789")):
        pass
    else:
        # assume already country digits or national without 0
        dial = COUNTRY_DIAL.get((country_code or "DE").upper(), "+49").lstrip("+")
        if not dig.startswith(dial):
            dig = dial + dig
    return f"https://wa.me/{dig}"


def telegram_href(handle: str | None) -> str | None:
    h = (handle or "").strip().lstrip("@")
    if not h:
        return None
    if h.startswith("http"):
        return h
    return f"https://t.me/{h}"


class BusinessProfileService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)

    def _path(self, order_id: str) -> Path:
        return self._memory / "store_admin" / order_id / "business_profile.json"

    def get(self, order_id: str) -> dict[str, Any]:
        path = self._path(order_id)
        base = default_business_profile()
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    base = self._merge(base, raw)
            except (OSError, json.JSONDecodeError):
                pass
        return {
            "ok": True,
            "order_id": order_id,
            "profile": base,
            "derived": self.derived_links(base),
            "note": (
                "Single source of truth — Website, Store, Email, PDF, and forms "
                "read this profile."
            ),
        }

    def _merge(self, base: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
        out = dict(base)
        for key, val in raw.items():
            if key == "address" and isinstance(val, dict):
                out["address"] = {**(out.get("address") or {}), **val}
            elif key == "social_links" and isinstance(val, dict):
                out["social_links"] = {**(out.get("social_links") or {}), **val}
            else:
                out[key] = val
        return out

    def update(self, order_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        current = self.get(order_id)["profile"]
        allowed = {
            "company_name",
            "phone_country_code",
            "phone_primary",
            "phone_secondary",
            "whatsapp",
            "telegram",
            "email_support",
            "email_orders",
            "hours",
            "logo_asset_id",
        }
        for key in allowed:
            if key in patch:
                val = patch[key]
                if val is None or (isinstance(val, str) and not val.strip()):
                    current[key] = None
                else:
                    current[key] = str(val).strip() if isinstance(val, str) else val
        if "address" in patch and isinstance(patch["address"], dict):
            addr = dict(current.get("address") or {})
            for k in ("street", "postal_code", "city", "country"):
                if k in patch["address"]:
                    v = patch["address"][k]
                    addr[k] = None if v in (None, "") else str(v).strip()
            current["address"] = addr
        if "social_links" in patch and isinstance(patch["social_links"], dict):
            social = dict(current.get("social_links") or {})
            for k, v in patch["social_links"].items():
                social[str(k)[:32]] = None if v in (None, "") else str(v).strip()[:200]
            current["social_links"] = social
        if current.get("phone_country_code"):
            current["phone_country_code"] = str(current["phone_country_code"]).upper()[:2]
        current["updated_at"] = _now()
        current["version"] = 1
        path = self._path(order_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "ok": True,
            "order_id": order_id,
            "profile": current,
            "derived": self.derived_links(current),
        }

    def derived_links(self, profile: dict[str, Any]) -> dict[str, Any]:
        cc = str(profile.get("phone_country_code") or "DE")
        return {
            "phone_primary_display": format_phone_display(profile.get("phone_primary"), cc),
            "phone_secondary_display": format_phone_display(profile.get("phone_secondary"), cc),
            "tel_primary": tel_href(profile.get("phone_primary"), cc),
            "tel_secondary": tel_href(profile.get("phone_secondary"), cc),
            "whatsapp_url": wa_me_href(profile.get("whatsapp") or profile.get("phone_primary"), cc),
            "telegram_url": telegram_href(profile.get("telegram")),
            "mailto_support": (
                f"mailto:{profile['email_support']}"
                if profile.get("email_support")
                else None
            ),
            "mailto_orders": (
                f"mailto:{profile['email_orders']}"
                if profile.get("email_orders")
                else None
            ),
        }

    def as_factory_contacts(self, order_id: str) -> dict[str, Any]:
        """Shape consumed by Website/Store factory footers and legal pages."""
        profile = self.get(order_id)["profile"]
        derived = self.derived_links(profile)
        addr = profile.get("address") or {}
        return {
            "company_name": profile.get("company_name"),
            "phone": derived.get("phone_primary_display") or profile.get("phone_primary"),
            "phone_secondary": derived.get("phone_secondary_display"),
            "email": profile.get("email_support") or profile.get("email_orders"),
            "email_orders": profile.get("email_orders"),
            "email_support": profile.get("email_support"),
            "whatsapp": profile.get("whatsapp"),
            "telegram": profile.get("telegram"),
            "tel": derived.get("tel_primary"),
            "whatsapp_url": derived.get("whatsapp_url"),
            "telegram_url": derived.get("telegram_url"),
            "address_line": ", ".join(
                str(x)
                for x in (
                    addr.get("street"),
                    " ".join(
                        str(p)
                        for p in (addr.get("postal_code"), addr.get("city"))
                        if p
                    ).strip()
                    or None,
                    addr.get("country"),
                )
                if x
            )
            or None,
            "hours": profile.get("hours"),
            "social_links": profile.get("social_links") or {},
            "logo_asset_id": profile.get("logo_asset_id"),
        }
