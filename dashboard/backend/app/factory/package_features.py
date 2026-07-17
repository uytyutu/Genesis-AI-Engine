"""Path A package → Factory landing feature matrix (honest delivery)."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from urllib.parse import quote_plus

from app.factory.analyzer import AnalysisResult


@dataclass(frozen=True)
class PackageFeatures:
    """What the HTML landing must include for a paid package."""

    package_id: str
    whatsapp: bool = True
    maps: bool = False
    testimonials: bool = False
    logo_slot: bool = False
    extended_seo: bool = False
    analytics: bool = False
    calculator: bool = False
    premium_design: bool = False
    contact_form: bool = True


def resolve_package_features(package_id: str | None) -> PackageFeatures:
    pid = (package_id or "basic").strip().lower()
    if pid not in ("basic", "business", "premium"):
        pid = "basic"
    if pid == "basic":
        return PackageFeatures(package_id="basic")
    if pid == "business":
        return PackageFeatures(
            package_id="business",
            maps=True,
            testimonials=True,
            logo_slot=True,
            extended_seo=True,
        )
    return PackageFeatures(
        package_id="premium",
        maps=True,
        testimonials=True,
        logo_slot=True,
        extended_seo=True,
        analytics=True,
        calculator=True,
        premium_design=True,
    )


def apply_order_contacts(
    analysis: AnalysisResult,
    *,
    business_name: str | None = None,
    phone: str | None = None,
    email: str | None = None,
) -> AnalysisResult:
    """Prefer real order contacts over analyzer placeholders."""
    name = (business_name or "").strip() or analysis.business_name
    ph = (phone or "").strip() or analysis.phone
    em = (email or "").strip() or analysis.email
    return replace(analysis, business_name=name, phone=ph, email=em)


def normalize_whatsapp_digits(raw: str) -> str:
    digits = re.sub(r"\D", "", (raw or "").strip())
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0") and len(digits) >= 10:
        digits = "49" + digits[1:]
    return digits


def whatsapp_href(whatsapp: str, phone_fallback: str = "") -> str:
    digits = normalize_whatsapp_digits(whatsapp) or normalize_whatsapp_digits(phone_fallback)
    if not digits:
        return "#contact"
    return f"https://wa.me/{digits}"


def maps_embed_src(*, business_name: str, city: str, street: str = "") -> str:
    query = " ".join(p for p in (business_name, street, city, "Deutschland") if p).strip()
    return f"https://maps.google.com/maps?q={quote_plus(query)}&z=14&output=embed"


def delivery_meta(features: PackageFeatures) -> dict:
    return {
        "package_id": features.package_id,
        "whatsapp": features.whatsapp,
        "maps": features.maps,
        "testimonials": features.testimonials,
        "logo_slot": features.logo_slot,
        "extended_seo": features.extended_seo,
        "analytics": features.analytics,
        "calculator": features.calculator,
        "premium_design": features.premium_design,
        "contact_form": features.contact_form,
    }
