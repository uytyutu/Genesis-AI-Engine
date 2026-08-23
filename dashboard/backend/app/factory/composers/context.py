"""Questionnaire-only context for Factory composers (architecture lock #3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class QuestionnaireContext:
    """Allowed data sources for Factory — no invented company facts."""

    business_name: str
    niche: str
    description: str = ""
    city: str = ""
    country: str = "DE"
    language: str = "de"
    package_id: str = "basic"
    services: tuple[str, ...] = ()
    advantages: tuple[str, ...] = ()
    phone: str = ""
    email: str = ""
    whatsapp: str = ""
    brand_style: str = "auto"
    market_code: str = "DE"
    # Lifetime project identity (upgrade unlocks features — same project).
    workspace_id: str = ""
    customer_id: str = ""
    extras: dict[str, Any] = field(default_factory=dict)

    def has_contact(self) -> bool:
        return bool(self.phone.strip() or self.email.strip() or self.whatsapp.strip())

    def primary_service(self) -> str:
        return self.services[0] if self.services else ""


def _tuple_list(raw: object) -> tuple[str, ...]:
    if isinstance(raw, (list, tuple)):
        items = [str(x).strip() for x in raw if str(x).strip()]
    elif isinstance(raw, str):
        text = raw.replace(";", "\n").replace("|", "\n")
        items = [ln.strip(" •-\t") for ln in text.splitlines() if ln.strip()]
    else:
        items = []
    out: list[str] = []
    for item in items:
        if item not in out:
            out.append(item)
        if len(out) >= 12:
            break
    return tuple(out)


def context_from_contacts(
    contacts: dict[str, Any],
    *,
    package_id: str | None = None,
    niche: str | None = None,
    business_name: str | None = None,
    description: str | None = None,
) -> QuestionnaireContext:
    pkg = str(package_id or contacts.get("package_id") or "basic").strip().lower() or "basic"
    name = (
        (business_name or "").strip()
        or str(contacts.get("business_name") or "").strip()
        or "Ihr Unternehmen"
    )
    niche_id = (niche or str(contacts.get("niche") or "generic")).strip().lower() or "generic"
    lang = str(
        contacts.get("ui_lang") or contacts.get("language") or "de"
    ).strip().lower() or "de"
    market = str(
        contacts.get("market_code") or contacts.get("country") or "DE"
    ).strip().upper() or "DE"
    return QuestionnaireContext(
        business_name=name,
        niche=niche_id,
        description=(description or str(contacts.get("description") or "")).strip(),
        city=str(contacts.get("city") or "").strip(),
        country=market,
        language=lang[:8],
        package_id=pkg,
        services=_tuple_list(contacts.get("services_list")),
        advantages=_tuple_list(contacts.get("advantages")),
        phone=str(contacts.get("phone") or "").strip(),
        email=str(contacts.get("email") or "").strip(),
        whatsapp=str(contacts.get("whatsapp") or contacts.get("phone") or "").strip(),
        brand_style=str(contacts.get("brand_style") or "auto").strip() or "auto",
        market_code=market,
        workspace_id=str(contacts.get("workspace_id") or "").strip(),
        customer_id=str(contacts.get("customer_id") or "").strip(),
    )


def merge_services(
    analysis_services: Sequence[str],
    questionnaire: Sequence[str],
) -> list[str]:
    """Prefer questionnaire services; never invent titles."""
    q = [s for s in questionnaire if str(s).strip()]
    if len(q) >= 2:
        return list(q)[:15]
    base = [s for s in analysis_services if str(s).strip()]
    return base[:15] if base else list(q)[:15]
